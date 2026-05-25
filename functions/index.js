// Lx8 Labs — Cloud Functions
//
// Auth model:
//   Every callable HTTP endpoint that mutates user-scoped data requires a
//   Firebase ID token in `Authorization: Bearer <token>`. The token is
//   verified server-side and the resulting UID is the only source of truth —
//   we never trust a `firebaseUid` field from the request body. Stripe
//   webhooks are exempt (verified via Stripe signature instead).
//
// Cryptography:
//   License keys are generated from crypto.randomBytes (CSPRNG), not
//   Math.random. The previous scheme produced ~46 guessable bits per key.

const { onRequest } = require("firebase-functions/v2/https");
const { onDocumentCreated } = require("firebase-functions/v2/firestore");
const crypto = require("crypto");
const fs = require("fs");
const { logger } = require("firebase-functions");

// ── Lazy SDK initialisation ─────────────────────────────────────────────
let stripeInstance = null;
const getStripe = () => {
  if (!stripeInstance) {
    stripeInstance = require("stripe")(process.env.STRIPE_SECRET_KEY || "sk_test_dummy");
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
const generateLicenseKey = () =>
  "LX8-" + crypto.randomBytes(8).toString("hex").toUpperCase() +
  "-"   + crypto.randomBytes(4).toString("hex").toUpperCase();

/**
 * Verify a Firebase ID token from the Authorization header. Returns the
 * decoded token on success, or null on absence/invalidity. Callers must
 * respond 401 when null.
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
    res.status(401).json({ error: "Unauthorized: missing or invalid Firebase ID token" });
    return null;
  }
  return decoded;
};

// ── 1. Stripe Webhook for License Provisioning ──────────────────────────
exports.stripeWebhook = onRequest({ maxInstances: 1, concurrency: 80 }, async (req, res) => {
  const sig = req.headers["stripe-signature"];
  let event;

  try {
    event = getStripe().webhooks.constructEvent(
      req.rawBody,
      sig,
      process.env.STRIPE_WEBHOOK_SECRET || "whsec_dummy"
    );
  } catch (err) {
    logger.error(`Webhook signature verification failed: ${err.message}`);
    res.status(400).send(`Webhook Error: ${err.message}`);
    return;
  }

  if (event.type === "checkout.session.completed") {
    const session = event.data.object;
    const firebaseUid = session.client_reference_id;

    if (firebaseUid) {
      const licenseKey = generateLicenseKey();
      await getAdmin().firestore()
        .collection("users").doc(firebaseUid)
        .collection("licenses").doc(licenseKey)
        .set({
          active: true,
          productId: session.metadata?.productId || "unknown",
          createdAt: getAdmin().firestore.FieldValue.serverTimestamp(),
          subscriptionId: session.subscription || null,
          stripeCustomerId: session.customer,
        });

      logger.info(`Provisioned license ${licenseKey} for user ${firebaseUid}`);
    } else {
      logger.warn("Checkout completed but no client_reference_id was provided.");
    }
  }

  res.json({ received: true });
});

// ── 2. Create Stripe Checkout Session ───────────────────────────────────
// Requires a valid Firebase ID token. The UID is taken from the verified
// token, never from the request body — previously, an attacker could pass
// an arbitrary `firebaseUid` and attach a paid license to any account.
exports.createCheckoutSession = onRequest({ cors: true, maxInstances: 1, concurrency: 80 }, async (req, res) => {
  if (req.method !== "POST") return res.status(405).send("Method Not Allowed");

  const decoded = await requireAuth(req, res);
  if (!decoded) return;

  const firebaseUid = decoded.uid;
  const email = decoded.email;
  const { productId } = req.body || {};
  if (!productId) return res.status(400).send("Missing productId");

  // Price IDs come from env, not from the source tree, so a public repo
  // never ships a real Stripe Price ID. Configure these via
  // `firebase functions:config:set` or the Functions runtime env.
  const priceMap = {
    prod_tupa_ide:       process.env.PRICE_TUPA,
    prod_bipartite_book: process.env.PRICE_BIPARTITE_BOOK,
    prod_aimem:          process.env.PRICE_AIMEM,
  };
  const priceId = priceMap[productId];
  if (!priceId) return res.status(400).send("Invalid or unconfigured productId");

  try {
    const session = await getStripe().checkout.sessions.create({
      payment_method_types: ["card"],
      customer_email: email || undefined,
      client_reference_id: firebaseUid,
      line_items: [{ price: priceId, quantity: 1 }],
      metadata: { productId },
      mode: "payment",
      success_url: "https://lx8labs.com/portal?success=true",
      cancel_url:  "https://lx8labs.com/portal?canceled=true",
    });
    res.json({ id: session.id, url: session.url });
  } catch (error) {
    logger.error("Stripe Session Error:", error);
    res.status(500).json({ error: error.message });
  }
});

// ── 3. Antigravity L1 Triage Agent (Support Queue) ──────────────────────
exports.triageAgent = onDocumentCreated({ document: "users/{userId}/support/{ticketId}", maxInstances: 1 }, async (event) => {
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
// Requires authentication. The UID is derived from the verified token; the
// caller may only mint tokens for their own licenseId.
exports.generateOfflineLicense = onRequest({ cors: true, maxInstances: 1, concurrency: 80 }, async (req, res) => {
  if (req.method !== "POST") return res.status(405).send("Method Not Allowed");

  const decoded = await requireAuth(req, res);
  if (!decoded) return;

  const firebaseUid = decoded.uid;
  const { licenseId } = req.body || {};
  if (!licenseId) return res.status(400).send("Missing licenseId");

  try {
    const licenseDoc = await getAdmin().firestore()
      .collection("users").doc(firebaseUid)
      .collection("licenses").doc(licenseId).get();

    if (!licenseDoc.exists || !licenseDoc.data().active) {
      return res.status(403).send("License not found or inactive");
    }

    const licenseData = licenseDoc.data();

    let privateKeyPem;
    try {
      privateKeyPem = process.env.LICENSE_PRIVATE_KEY ||
        fs.readFileSync("./enterprise_private.pem", "utf8");
    } catch (e) {
      logger.error("Missing private key:", e);
      return res.status(500).send("Critical Error: Enterprise Private Key not configured.");
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
    logger.error("Offline License Generation Error:", error);
    res.status(500).json({ error: error.message });
  }
});

// ── 5. Global SSO Session Cookie Generator ──────────────────────────────
// Verifies the provided ID token via the admin SDK before exchanging it for
// a session cookie. (Unauthenticated callers can't forge a valid token.)
exports.createSessionCookie = onRequest({ cors: true, maxInstances: 1, concurrency: 80 }, async (req, res) => {
  if (req.method !== "POST") return res.status(405).send("Method Not Allowed");

  const { idToken } = req.body || {};
  if (!idToken) return res.status(400).send("Missing idToken");

  try {
    // Verify the token is current; createSessionCookie also rejects bad
    // tokens, but verifying first gives us a clearer error code.
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
    logger.error("SSO Cookie Generation Error:", error);
    res.status(401).json({ error: "Invalid or expired ID token" });
  }
});

// ── 6. Client Management: Device Tracking & Registration ────────────────
exports.registerClientDevice = onRequest({ cors: true, maxInstances: 1, concurrency: 80 }, async (req, res) => {
  if (req.method !== "POST") return res.status(405).send("Method Not Allowed");

  const decoded = await requireAuth(req, res);
  if (!decoded) return;

  const firebaseUid = decoded.uid;
  const { licenseId, hardwareFingerprint, osVersion } = req.body || {};
  if (!licenseId || !hardwareFingerprint) return res.status(400).send("Missing required fields");

  try {
    const licenseRef = getAdmin().firestore()
      .collection("users").doc(firebaseUid)
      .collection("licenses").doc(licenseId);
    const licenseDoc = await licenseRef.get();

    if (!licenseDoc.exists || !licenseDoc.data().active) {
      return res.status(403).send("License not found or inactive");
    }

    const devicesRef = licenseRef.collection("devices");

    await getAdmin().firestore().runTransaction(async (transaction) => {
      const snapshot = await transaction.get(devicesRef);
      const devices = snapshot.docs;

      const deviceExists = devices.find((d) => d.id === hardwareFingerprint);

      if (!deviceExists && devices.length >= 3) {
        throw new Error("Device limit exceeded. Max 3 devices allowed per license.");
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
    logger.error("Device Registration Error:", error);
    res.status(400).json({ error: error.message });
  }
});

// ── 7. Client Management: Revoke Device ─────────────────────────────────
exports.revokeClientDevice = onRequest({ cors: true, maxInstances: 1, concurrency: 80 }, async (req, res) => {
  if (req.method !== "POST") return res.status(405).send("Method Not Allowed");

  const decoded = await requireAuth(req, res);
  if (!decoded) return;

  const firebaseUid = decoded.uid;
  const { licenseId, hardwareFingerprint } = req.body || {};
  if (!licenseId || !hardwareFingerprint) return res.status(400).send("Missing required fields");

  try {
    await getAdmin().firestore()
      .collection("users").doc(firebaseUid)
      .collection("licenses").doc(licenseId)
      .collection("devices").doc(hardwareFingerprint).delete();

    logger.info(`Revoked device ${hardwareFingerprint} for license ${licenseId}`);
    res.json({ status: "success" });
  } catch (error) {
    logger.error("Device Revocation Error:", error);
    res.status(500).json({ error: error.message });
  }
});
