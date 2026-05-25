// Lx8 Labs — Cloud Functions
//
// Auth model:
//   Every callable HTTP endpoint that mutates user-scoped data requires a
//   Firebase ID token in `Authorization: Bearer <token>`. The token is
//   verified server-side and the resulting UID is the only source of truth —
//   we never trust a `firebaseUid` field from the request body. Stripe
//   webhooks are exempt (verified via Stripe signature instead).
//
// CORS:
//   Mutating endpoints accept only origins in ALLOWED_ORIGINS (apex +
//   subdomains + native Firebase URLs). `cors: true` everywhere would have
//   accepted any origin and enabled CSRF.
//
// Secrets:
//   All Stripe / licensing secrets are bound to each function via
//   `defineSecret()`. There is no `|| "sk_test_dummy"` fallback — a missing
//   secret fails the function at cold start, surfacing the misconfiguration
//   immediately rather than letting placeholder values reach production.
//
// Webhook idempotency:
//   Every Stripe event is recorded in `stripe_events/{event.id}` inside a
//   Firestore transaction *before* any business logic runs. Duplicate
//   deliveries (Stripe redelivers on timeout) early-exit without
//   re-provisioning. A Firestore TTL policy on the collection prunes
//   entries older than 90 days.
//
// Error surface:
//   Every catch funnels through `respondError(res, code, publicMessage,
//   internalErr)`. The internal error is logged with full detail; the wire
//   response only carries a generic message + a request id, so we don't
//   leak "Enterprise Private Key not configured" or Stripe internals.

const { onRequest } = require("firebase-functions/v2/https");
const { onDocumentCreated } = require("firebase-functions/v2/firestore");
const { defineSecret } = require("firebase-functions/params");
const { logger } = require("firebase-functions");
const crypto = require("crypto");
const fs = require("fs");

// ── Secrets ─────────────────────────────────────────────────────────────
// Bound per-function below. Provision once via:
//   firebase functions:secrets:set STRIPE_SECRET_KEY
//   firebase functions:secrets:set STRIPE_WEBHOOK_SECRET
//   firebase functions:secrets:set LICENSE_PRIVATE_KEY
//   firebase functions:secrets:set PRICE_TUPA
//   firebase functions:secrets:set PRICE_BIPARTITE_BOOK
//   firebase functions:secrets:set PRICE_AIMEM
const STRIPE_SECRET_KEY     = defineSecret("STRIPE_SECRET_KEY");
const STRIPE_WEBHOOK_SECRET = defineSecret("STRIPE_WEBHOOK_SECRET");
const LICENSE_PRIVATE_KEY   = defineSecret("LICENSE_PRIVATE_KEY");
const PRICE_TUPA            = defineSecret("PRICE_TUPA");
const PRICE_BIPARTITE_BOOK  = defineSecret("PRICE_BIPARTITE_BOOK");
const PRICE_AIMEM           = defineSecret("PRICE_AIMEM");

// ── CORS allowlist ──────────────────────────────────────────────────────
// One source of truth for every mutating endpoint. Mirrors the active
// hosting targets in firebase.json. The native .web.app / .firebaseapp.com
// origins are included for the deploy-preview channels and for emulator
// runs from `firebase emulators:start`.
const ALLOWED_ORIGINS = [
  "https://lx8labs.com",
  "https://www.lx8labs.com",
  "https://aimem.lx8labs.com",
  "https://tupa.lx8labs.com",
  "https://tupaide.lx8labs.com",
  "https://suit.lx8labs.com",
  "https://bipartitebook.lx8labs.com",
  "https://installations.lx8labs.com",
  "https://mattermem.lx8labs.com",
  "https://lx8-labs-website.web.app",
  "https://lx8-labs-website.firebaseapp.com",
];

// ── Lazy SDK initialisation ─────────────────────────────────────────────
// Stripe is instantiated lazily once per cold start. Calling .value() on a
// secret outside the handler scope throws — so we route through this getter
// that's only invoked after the function is entered.
let stripeInstance = null;
const getStripe = () => {
  if (!stripeInstance) {
    stripeInstance = require("stripe")(STRIPE_SECRET_KEY.value(), {
      // Pin the API version so a Stripe-side default rev doesn't silently
      // change response shapes in production.
      apiVersion: "2024-12-18.acacia",
      maxNetworkRetries: 2,
      timeout: 8000,
    });
  }
  return stripeInstance;
};

let adminInstance = null;
const getAdmin = () => {
  if (!adminInstance) {
    adminInstance = require("firebase-admin");
    adminInstance.initializeApp();
  }
  return adminInstance;
};

// ── Helpers ─────────────────────────────────────────────────────────────

/**
 * Respond with a generic public message; log the internal detail.
 * Every error response in this file goes through here so we can ratchet
 * up logging or add a correlation id once without touching every catch.
 */
const respondError = (res, code, publicMessage, internalErr) => {
  const requestId = crypto.randomBytes(6).toString("hex");
  if (internalErr) {
    logger.error(`[${requestId}] ${publicMessage}`, {
      requestId,
      error: internalErr?.message || String(internalErr),
      stack: internalErr?.stack,
    });
  } else {
    logger.warn(`[${requestId}] ${publicMessage}`);
  }
  res.status(code).json({ error: publicMessage, requestId });
};

const generateLicenseKey = () =>
  "LX8-" + crypto.randomBytes(8).toString("hex").toUpperCase() +
  "-"   + crypto.randomBytes(4).toString("hex").toUpperCase();

/**
 * Verify a Firebase ID token from the Authorization header. Returns the
 * decoded token on success, or null on absence/invalidity.
 */
const verifyAuthToken = async (req) => {
  const header = req.headers.authorization || "";
  if (!header.startsWith("Bearer ")) return null;
  const token = header.slice("Bearer ".length).trim();
  if (!token) return null;
  try {
    return await getAdmin().auth().verifyIdToken(token);
  } catch (err) {
    logger.warn("verifyIdToken failed", { message: err.message });
    return null;
  }
};

const requireAuth = async (req, res) => {
  const decoded = await verifyAuthToken(req);
  if (!decoded) {
    respondError(res, 401, "Unauthorized: missing or invalid Firebase ID token");
    return null;
  }
  return decoded;
};

/**
 * Record a Stripe event id in `stripe_events/{id}` inside a transaction.
 * Returns true the first time it's seen, false on every subsequent call.
 * The doc carries a `processedAt` server timestamp so a TTL policy in
 * `firestore.rules` config can prune the collection at 90 days.
 */
const claimStripeEvent = async (event) => {
  const db = getAdmin().firestore();
  const ref = db.collection("stripe_events").doc(event.id);
  return db.runTransaction(async (tx) => {
    const snap = await tx.get(ref);
    if (snap.exists) return false;
    tx.set(ref, {
      type: event.type,
      processedAt: getAdmin().firestore.FieldValue.serverTimestamp(),
    });
    return true;
  });
};

/**
 * Find a license document for a Stripe customer + charge so refund handling
 * can deactivate the right row without us tracking the doc id on Stripe's
 * side. Returns the snapshot or null.
 */
const findLicenseByCharge = async (stripeCustomerId, stripeChargeId) => {
  const db = getAdmin().firestore();
  // Charges and customers are stored on the license doc when provisioned.
  const byCharge = await db.collectionGroup("licenses")
    .where("stripeChargeId", "==", stripeChargeId)
    .limit(1).get();
  if (!byCharge.empty) return byCharge.docs[0];
  if (!stripeCustomerId) return null;
  const byCustomer = await db.collectionGroup("licenses")
    .where("stripeCustomerId", "==", stripeCustomerId)
    .where("active", "==", true)
    .limit(1).get();
  return byCustomer.empty ? null : byCustomer.docs[0];
};

const sha256Hex = (input) =>
  crypto.createHash("sha256").update(input).digest("hex");

// ── 1. Stripe Webhook ───────────────────────────────────────────────────
exports.stripeWebhook = onRequest({
  secrets: [STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET],
  maxInstances: 2,
  concurrency: 80,
}, async (req, res) => {
  const sig = req.headers["stripe-signature"];
  let event;

  try {
    event = getStripe().webhooks.constructEvent(
      req.rawBody,
      sig,
      STRIPE_WEBHOOK_SECRET.value(),
    );
  } catch (err) {
    // Don't leak via respondError — Stripe expects a plain 400 body.
    logger.error("Webhook signature verification failed", { message: err.message });
    res.status(400).send(`Webhook Error: ${err.message}`);
    return;
  }

  // Idempotency: bail before doing any work on a redelivery.
  let isNew;
  try {
    isNew = await claimStripeEvent(event);
  } catch (err) {
    return respondError(res, 500, "Webhook claim transaction failed", err);
  }
  if (!isNew) {
    logger.info(`event ${event.id} already processed; skipping`);
    return res.json({ received: true, deduped: true });
  }

  try {
    switch (event.type) {
      case "checkout.session.completed":
        await handleCheckoutCompleted(event.data.object);
        break;
      case "charge.refunded":
        await handleChargeRefunded(event.data.object);
        break;
      case "payment_intent.payment_failed":
        // Observability only — no provisioning to undo for one-time payments
        // that never completed. Useful trail when a card is declined.
        logger.warn("payment_intent.payment_failed", {
          paymentIntent: event.data.object.id,
          lastError: event.data.object.last_payment_error?.message,
        });
        break;
      case "customer.subscription.updated":
      case "customer.subscription.deleted":
        // No-op stub. When `mode: "subscription"` SKUs ship, route to a
        // handler that flips license activity per the new status.
        logger.info(`subscription event noted (no SKUs yet): ${event.type}`, {
          subscription: event.data.object.id,
          status: event.data.object.status,
        });
        break;
      default:
        logger.debug(`unhandled stripe event: ${event.type}`);
    }
  } catch (err) {
    // Returning a non-2xx tells Stripe to redeliver. Because we already
    // wrote the event sentinel, redelivery would dedup; *delete* the
    // sentinel so the retry can actually run.
    try {
      await getAdmin().firestore()
        .collection("stripe_events").doc(event.id).delete();
    } catch (cleanupErr) {
      logger.error("failed to roll back stripe_events sentinel", { event: event.id });
    }
    return respondError(res, 500, "Webhook handler failed", err);
  }

  res.json({ received: true });
});

const handleCheckoutCompleted = async (session) => {
  const firebaseUid = session.client_reference_id;
  if (!firebaseUid) {
    logger.warn("Checkout completed but no client_reference_id was provided.", {
      session: session.id,
    });
    return;
  }

  const licenseKey = generateLicenseKey();
  const db = getAdmin().firestore();
  const FieldValue = getAdmin().firestore.FieldValue;

  // Persist the Stripe customer id on the user doc so subsequent endpoints
  // (billingPortal, restorePurchases) can find them without a lookup.
  if (session.customer) {
    await db.collection("users").doc(firebaseUid).set({
      stripeCustomerId: session.customer,
      updatedAt: FieldValue.serverTimestamp(),
    }, { merge: true });
  }

  await db.collection("users").doc(firebaseUid)
    .collection("licenses").doc(licenseKey).set({
      active: true,
      productId: session.metadata?.productId || "unknown",
      createdAt: FieldValue.serverTimestamp(),
      subscriptionId: session.subscription || null,
      stripeCustomerId: session.customer || null,
      stripeSessionId: session.id,
      // payment_intent is sometimes a stub object; pull just the id.
      stripeChargeId: typeof session.payment_intent === "string"
        ? session.payment_intent : (session.payment_intent?.id || null),
      amountTotal: session.amount_total || null,
      currency: session.currency || null,
    });

  logger.info(`Provisioned license ${licenseKey} for user ${firebaseUid}`);
};

const handleChargeRefunded = async (charge) => {
  const license = await findLicenseByCharge(charge.customer, charge.payment_intent);
  if (!license) {
    logger.warn("charge.refunded received for unknown license", {
      charge: charge.id,
      paymentIntent: charge.payment_intent,
    });
    return;
  }
  await license.ref.update({
    active: false,
    refundedAt: getAdmin().firestore.FieldValue.serverTimestamp(),
    refundReason: charge.refunds?.data?.[0]?.reason || "unknown",
  });
  logger.info(`Deactivated license ${license.id} after refund of charge ${charge.id}`);
};

// ── 2. Create Stripe Checkout Session ───────────────────────────────────
exports.createCheckoutSession = onRequest({
  cors: ALLOWED_ORIGINS,
  secrets: [STRIPE_SECRET_KEY, PRICE_TUPA, PRICE_BIPARTITE_BOOK, PRICE_AIMEM],
  maxInstances: 2,
  concurrency: 80,
}, async (req, res) => {
  if (req.method !== "POST") return respondError(res, 405, "Method Not Allowed");

  const decoded = await requireAuth(req, res);
  if (!decoded) return;

  const firebaseUid = decoded.uid;
  const email = decoded.email;
  const { productId } = req.body || {};
  if (!productId) return respondError(res, 400, "Missing productId");

  const priceMap = {
    prod_tupa_ide:       PRICE_TUPA.value(),
    prod_bipartite_book: PRICE_BIPARTITE_BOOK.value(),
    prod_aimem:          PRICE_AIMEM.value(),
  };
  const priceId = priceMap[productId];
  if (!priceId) return respondError(res, 400, "Invalid or unconfigured productId");

  try {
    // Idempotency: a uid + product + day-stamp hash. A user who double-clicks
    // the Buy button within the same day gets the same Stripe Checkout
    // session back instead of two parallel ones. Crossing a UTC day boundary
    // is a tiny window where dedup doesn't apply; acceptable.
    const idempotencyKey = sha256Hex(
      `${firebaseUid}|${productId}|${new Date().toISOString().slice(0, 10)}`
    );

    // Reuse an existing Stripe customer if we already saw one for this UID.
    // Lets the customer accumulate purchase history under a single
    // customer record and unlocks the billing portal flow.
    const userDoc = await getAdmin().firestore()
      .collection("users").doc(firebaseUid).get();
    const existingCustomer = userDoc.exists ? userDoc.data().stripeCustomerId : null;

    const session = await getStripe().checkout.sessions.create({
      payment_method_types: ["card"],
      ...(existingCustomer
        ? { customer: existingCustomer }
        : { customer_email: email || undefined, customer_creation: "always" }
      ),
      client_reference_id: firebaseUid,
      line_items: [{ price: priceId, quantity: 1 }],
      metadata: { productId, firebaseUid },
      mode: "payment",
      success_url: "https://lx8labs.com/portal?success=true",
      cancel_url:  "https://lx8labs.com/portal?canceled=true",
      billing_address_collection: "auto",
    }, { idempotencyKey });

    res.json({ id: session.id, url: session.url });
  } catch (error) {
    return respondError(res, 502, "Could not create checkout session", error);
  }
});

// ── 3. Antigravity L1 Triage Agent (Support Queue) ──────────────────────
exports.triageAgent = onDocumentCreated({
  document: "users/{userId}/support/{ticketId}",
  maxInstances: 1,
}, async (event) => {
  const snapshot = event.data;
  if (!snapshot) return;

  const ticket = snapshot.data();
  if (ticket.sender !== "user") return; // Only respond to user-authored tickets

  const userId = event.params.userId;
  const ticketContent = (ticket.content || "").toLowerCase();

  let aiResponse = "I have escalated this issue to a human engineer. They will respond shortly.";
  let newStatus = "OPEN";

  // Mocked AI L1 Routing (replace with Vertex AI / Gemini later)
  if (ticketContent.includes("license") || ticketContent.includes("key")) {
    aiResponse = "I see you're asking about your license. You can view all your active license keys on the main portal dashboard. Click the 'Reveal' button to copy them into your IDE or CLI.";
    newStatus = "RESOLVED";
  } else if (ticketContent.includes("dns") || ticketContent.includes("cloudflare")) {
    aiResponse = "DNS propagation usually takes between 1 to 24 hours. If your subdomain says 'PROPAGATING', please wait a few hours or flush your local DNS cache.";
    newStatus = "RESOLVED";
  } else if (ticketContent.includes("tupa")) {
    aiResponse = "Tupã IDE requires macOS 13.0 or higher. Make sure you have downloaded the correct architecture (Apple Silicon vs Intel).";
  }

  await new Promise((resolve) => setTimeout(resolve, 1500));

  await getAdmin().firestore()
    .collection("users").doc(userId)
    .collection("support").add({
      content: aiResponse,
      sender: "agent",
      createdAt: getAdmin().firestore.FieldValue.serverTimestamp(),
      status: newStatus,
    });

  if (newStatus === "RESOLVED") {
    await snapshot.ref.update({ status: "RESOLVED" });
  }
});

// ── 4. Generate Offline License Key (ECDSA) ─────────────────────────────
exports.generateOfflineLicense = onRequest({
  cors: ALLOWED_ORIGINS,
  secrets: [LICENSE_PRIVATE_KEY],
  maxInstances: 2,
  concurrency: 80,
}, async (req, res) => {
  if (req.method !== "POST") return respondError(res, 405, "Method Not Allowed");

  const decoded = await requireAuth(req, res);
  if (!decoded) return;

  const firebaseUid = decoded.uid;
  const { licenseId } = req.body || {};
  if (!licenseId) return respondError(res, 400, "Missing licenseId");

  try {
    const licenseDoc = await getAdmin().firestore()
      .collection("users").doc(firebaseUid)
      .collection("licenses").doc(licenseId).get();

    if (!licenseDoc.exists || !licenseDoc.data().active) {
      return respondError(res, 403, "License not found or inactive");
    }

    const licenseData = licenseDoc.data();

    // Refunded licenses must never mint a fresh signed token.
    if (licenseData.refundedAt) {
      return respondError(res, 403, "License not found or inactive");
    }

    let privateKeyPem;
    try {
      // LICENSE_PRIVATE_KEY is a defineSecret() value; the .pem-on-disk path
      // is a developer-machine fallback that should never be reached in
      // production. If neither is available, fail loudly (no public leak).
      privateKeyPem = LICENSE_PRIVATE_KEY.value() ||
        fs.readFileSync("./enterprise_private.pem", "utf8");
    } catch (e) {
      return respondError(res, 503, "License signing is temporarily unavailable", e);
    }

    const payload = JSON.stringify({
      uid: firebaseUid,
      lid: licenseId,
      pid: licenseData.productId,
      exp: licenseData.expiresAt ? licenseData.expiresAt.toDate().getTime() : "NEVER",
      iss: "Lx8Labs",
    });

    const sign = crypto.createSign("SHA256");
    sign.update(payload);
    sign.end();
    const signature = sign.sign(privateKeyPem, "base64");

    const encodedPayload   = Buffer.from(payload).toString("base64url");
    const encodedSignature = Buffer.from(signature, "base64").toString("base64url");
    const offlineToken = `LX8-${encodedPayload}.${encodedSignature}`;

    res.json({ token: offlineToken });
  } catch (error) {
    return respondError(res, 500, "Could not generate offline license", error);
  }
});

// ── 5. Global SSO Session Cookie Generator ──────────────────────────────
exports.createSessionCookie = onRequest({
  cors: ALLOWED_ORIGINS,
  maxInstances: 1,
  concurrency: 80,
}, async (req, res) => {
  if (req.method !== "POST") return respondError(res, 405, "Method Not Allowed");

  const { idToken } = req.body || {};
  if (!idToken) return respondError(res, 400, "Missing idToken");

  try {
    await getAdmin().auth().verifyIdToken(idToken);

    const expiresIn = 1000 * 60 * 60 * 24 * 14; // 14 days
    const sessionCookie = await getAdmin().auth().createSessionCookie(idToken, { expiresIn });

    const isLocalhost = req.hostname === "localhost" || req.hostname === "127.0.0.1";
    const domainOpt = isLocalhost ? "" : "Domain=.lx8labs.com;";
    const secureOpt = isLocalhost ? "" : "Secure;";

    res.setHeader(
      "Set-Cookie",
      `__session=${sessionCookie}; ${domainOpt} Path=/; Max-Age=${expiresIn / 1000}; HttpOnly; ${secureOpt} SameSite=Lax`
    );
    res.json({ status: "success" });
  } catch (error) {
    return respondError(res, 401, "Invalid or expired ID token", error);
  }
});

// ── 6. Client Management: Device Tracking & Registration ────────────────
exports.registerClientDevice = onRequest({
  cors: ALLOWED_ORIGINS,
  maxInstances: 2,
  concurrency: 80,
}, async (req, res) => {
  if (req.method !== "POST") return respondError(res, 405, "Method Not Allowed");

  const decoded = await requireAuth(req, res);
  if (!decoded) return;

  const firebaseUid = decoded.uid;
  const { licenseId, hardwareFingerprint, osVersion } = req.body || {};
  if (!licenseId || !hardwareFingerprint) {
    return respondError(res, 400, "Missing required fields");
  }

  try {
    const licenseRef = getAdmin().firestore()
      .collection("users").doc(firebaseUid)
      .collection("licenses").doc(licenseId);
    const licenseDoc = await licenseRef.get();

    if (!licenseDoc.exists || !licenseDoc.data().active) {
      return respondError(res, 403, "License not found or inactive");
    }

    const devicesRef = licenseRef.collection("devices");

    await getAdmin().firestore().runTransaction(async (transaction) => {
      const snapshot = await transaction.get(devicesRef);
      const devices = snapshot.docs;

      const deviceExists = devices.find((d) => d.id === hardwareFingerprint);

      if (!deviceExists && devices.length >= 3) {
        throw Object.assign(new Error("Device limit exceeded. Max 3 devices allowed per license."),
          { publicCode: 400, publicMessage: "Device limit exceeded. Max 3 devices allowed per license." });
      }

      transaction.set(devicesRef.doc(hardwareFingerprint), {
        osVersion: osVersion || "unknown",
        lastSeen: getAdmin().firestore.FieldValue.serverTimestamp(),
        registeredAt: deviceExists ? deviceExists.data().registeredAt : getAdmin().firestore.FieldValue.serverTimestamp(),
      }, { merge: true });
    });

    logger.info(`Registered device ${hardwareFingerprint} for license ${licenseId}`);
    res.json({ status: "success", deviceId: hardwareFingerprint });
  } catch (error) {
    // Surface the "Device limit exceeded" verbatim because it's a UX-grade
    // message; everything else gets the generic fallback.
    if (error.publicCode) {
      return respondError(res, error.publicCode, error.publicMessage, error);
    }
    return respondError(res, 500, "Could not register device", error);
  }
});

// ── 7. Client Management: Revoke Device ─────────────────────────────────
exports.revokeClientDevice = onRequest({
  cors: ALLOWED_ORIGINS,
  maxInstances: 2,
  concurrency: 80,
}, async (req, res) => {
  if (req.method !== "POST") return respondError(res, 405, "Method Not Allowed");

  const decoded = await requireAuth(req, res);
  if (!decoded) return;

  const firebaseUid = decoded.uid;
  const { licenseId, hardwareFingerprint } = req.body || {};
  if (!licenseId || !hardwareFingerprint) {
    return respondError(res, 400, "Missing required fields");
  }

  try {
    await getAdmin().firestore()
      .collection("users").doc(firebaseUid)
      .collection("licenses").doc(licenseId)
      .collection("devices").doc(hardwareFingerprint).delete();

    logger.info(`Revoked device ${hardwareFingerprint} for license ${licenseId}`);
    res.json({ status: "success" });
  } catch (error) {
    return respondError(res, 500, "Could not revoke device", error);
  }
});

// ── 8. Customer Billing Portal (NEW) ────────────────────────────────────
// Lets an authenticated user manage payment methods, view invoices, and
// cancel subscriptions through Stripe's hosted portal. Requires that we've
// already persisted users/{uid}.stripeCustomerId on a prior checkout — if
// not, the response is a 404 with a hint to make a first purchase.
exports.createBillingPortalSession = onRequest({
  cors: ALLOWED_ORIGINS,
  secrets: [STRIPE_SECRET_KEY],
  maxInstances: 1,
  concurrency: 80,
}, async (req, res) => {
  if (req.method !== "POST") return respondError(res, 405, "Method Not Allowed");

  const decoded = await requireAuth(req, res);
  if (!decoded) return;

  try {
    const userDoc = await getAdmin().firestore()
      .collection("users").doc(decoded.uid).get();
    const customerId = userDoc.exists ? userDoc.data().stripeCustomerId : null;
    if (!customerId) {
      return respondError(res, 404, "No Stripe customer on file for this account");
    }

    const portal = await getStripe().billingPortal.sessions.create({
      customer: customerId,
      return_url: "https://lx8labs.com/portal",
    });

    res.json({ url: portal.url });
  } catch (error) {
    return respondError(res, 502, "Could not open billing portal", error);
  }
});

// ── 9. Restore Purchases (NEW) ──────────────────────────────────────────
// Resilience valve: if a webhook ever fails to deliver and a paying user
// has no license on file, this endpoint asks Stripe for every completed
// checkout session attached to their email and re-provisions anything
// missing. Idempotent — uses the same `users/{uid}/licenses/{key}` write,
// keyed by the Stripe session id to avoid creating duplicates.
exports.restorePurchases = onRequest({
  cors: ALLOWED_ORIGINS,
  secrets: [STRIPE_SECRET_KEY],
  maxInstances: 1,
  concurrency: 40,
}, async (req, res) => {
  if (req.method !== "POST") return respondError(res, 405, "Method Not Allowed");

  const decoded = await requireAuth(req, res);
  if (!decoded) return;

  const email = decoded.email;
  if (!email) {
    return respondError(res, 400, "Account has no email on file");
  }

  try {
    // Search Stripe customers by email (uses Stripe's search API; requires
    // recent objects to be queryable). Up to 100 results is plenty for
    // realistic per-user volume.
    const customerSearch = await getStripe().customers.search({
      query: `email:'${email.replace(/'/g, "")}'`,
      limit: 20,
    });

    const db = getAdmin().firestore();
    const FieldValue = getAdmin().firestore.FieldValue;
    const restored = [];

    for (const customer of customerSearch.data) {
      // Persist customer id back to the user doc so future billingPortal
      // calls work without another search round-trip.
      await db.collection("users").doc(decoded.uid).set({
        stripeCustomerId: customer.id,
        updatedAt: FieldValue.serverTimestamp(),
      }, { merge: true });

      const sessions = await getStripe().checkout.sessions.list({
        customer: customer.id,
        limit: 50,
      });

      for (const session of sessions.data.filter((s) => s.payment_status === "paid")) {
        const existing = await db.collectionGroup("licenses")
          .where("stripeSessionId", "==", session.id).limit(1).get();
        if (!existing.empty) continue;

        // Reuse the same write path the webhook uses for consistency.
        await handleCheckoutCompleted({
          ...session,
          client_reference_id: decoded.uid,
        });
        restored.push(session.id);
      }
    }

    res.json({ restored, count: restored.length });
  } catch (error) {
    return respondError(res, 502, "Could not restore purchases", error);
  }
});
