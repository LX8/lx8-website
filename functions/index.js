const { onRequest } = require("firebase-functions/v2/https");
const { onDocumentCreated } = require("firebase-functions/v2/firestore");
const crypto = require("crypto");
const fs = require("fs");
const { logger } = require("firebase-functions");
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

// 1. Stripe Webhook for License Provisioning
exports.stripeWebhook = onRequest({ maxInstances: 1, concurrency: 80 }, async (req, res) => {
  const sig = req.headers["stripe-signature"];
  let event;

  try {
    // Verify the webhook signature securely
    event = getStripe().webhooks.constructEvent(req.rawBody, sig, process.env.STRIPE_WEBHOOK_SECRET || "whsec_dummy");
  } catch (err) {
    logger.error(`Webhook Error: ${err.message}`);
    res.status(400).send(`Webhook Error: ${err.message}`);
    return;
  }

  // Handle successful checkout session
  if (event.type === "checkout.session.completed") {
    const session = event.data.object;
    
    // We assume the client passed their Firebase Auth UID in the client_reference_id
    const firebaseUid = session.client_reference_id;
    
    if (firebaseUid) {
      // 1. Generate a secure License Key
      const licenseKey = "LX8-" + Math.random().toString(36).substr(2, 9).toUpperCase() + "-" + Date.now().toString(36).toUpperCase();
      
      // 2. Save to Firestore under the user's profile
      await getAdmin().firestore().collection("users").doc(firebaseUid).collection("licenses").doc(licenseKey).set({
        active: true,
        productId: session.metadata?.productId || "unknown",
        createdAt: getAdmin().firestore.FieldValue.serverTimestamp(),
        subscriptionId: session.subscription || null,
        stripeCustomerId: session.customer
      });

      logger.info(`Successfully provisioned license ${licenseKey} for user ${firebaseUid}`);
    } else {
      logger.warn("Checkout completed, but no client_reference_id (Firebase UID) was provided.");
    }
  }

  res.json({ received: true });
});

// 2. Create Stripe Checkout Session
exports.createCheckoutSession = onRequest({ cors: true, maxInstances: 1, concurrency: 80 }, async (req, res) => {
  if (req.method !== 'POST') {
    return res.status(405).send('Method Not Allowed');
  }

  const { firebaseUid, productId, email } = req.body;

  if (!firebaseUid || !productId) {
    return res.status(400).send('Missing required fields');
  }

  // Price Map (In a real app, fetch from Firestore or Stripe Products API)
  const priceMap = {
    'prod_tupa_ide': 'price_placeholder_tupa', // Replace with real Stripe Price ID
    'prod_bipartite_book': 'price_placeholder_book', 
    'prod_aimem': 'price_placeholder_aimem'
  };

  const priceId = priceMap[productId];
  if (!priceId) {
    return res.status(400).send('Invalid productId');
  }

  try {
    const session = await getStripe().checkout.sessions.create({
      payment_method_types: ['card'],
      customer_email: email || undefined,
      client_reference_id: firebaseUid, // Crucial for webhook association
      line_items: [
        {
          price: priceId,
          quantity: 1,
        },
      ],
      metadata: {
        productId: productId
      },
      mode: 'payment',
      success_url: 'https://lx8labs.com/portal?success=true',
      cancel_url: 'https://lx8labs.com/portal?canceled=true',
    });

    res.json({ id: session.id, url: session.url });
  } catch (error) {
    logger.error('Stripe Session Error:', error);
    res.status(500).json({ error: error.message });
  }
});

// 3. Antigravity L1 Triage Agent (Support Queue)
exports.triageAgent = onDocumentCreated({ document: "users/{userId}/support/{ticketId}", maxInstances: 1 }, async (event) => {
  const snapshot = event.data;
  if (!snapshot) return;

  const ticket = snapshot.data();
  // Prevent infinite loops: only respond to user tickets
  if (ticket.sender !== 'user') return;

  const userId = event.params.userId;
  const ticketContent = ticket.content.toLowerCase();
  
  let aiResponse = "I have escalated this issue to a human engineer. They will respond shortly.";
  let newStatus = "OPEN";

  // Mocked AI L1 Routing (Replace with Vertex AI/Gemini later)
  if (ticketContent.includes("license") || ticketContent.includes("key")) {
    aiResponse = "I see you're asking about your license. You can view all your active license keys on the main portal dashboard. Click the 'Reveal' button to copy them into your IDE or CLI.";
    newStatus = "RESOLVED";
  } else if (ticketContent.includes("dns") || ticketContent.includes("cloudflare")) {
    aiResponse = "DNS propagation usually takes between 1 to 24 hours. If your subdomain says 'PROPAGATING', please wait a few hours or flush your local DNS cache.";
    newStatus = "RESOLVED";
  } else if (ticketContent.includes("tupa")) {
    aiResponse = "Tupã IDE requires macOS 13.0 or higher. Make sure you have downloaded the correct architecture (Apple Silicon vs Intel).";
  }

  // Simulate AI "Thinking" delay before replying
  await new Promise(resolve => setTimeout(resolve, 1500));

  await getAdmin().firestore().collection("users").doc(userId).collection("support").add({
    content: aiResponse,
    sender: 'agent',
    createdAt: getAdmin().firestore.FieldValue.serverTimestamp(),
    status: newStatus
  });

  // Mark original ticket if resolved
  if (newStatus === "RESOLVED") {
    await snapshot.ref.update({ status: "RESOLVED" });
  }
});

// 4. Generate Offline License Key (ECDSA)
exports.generateOfflineLicense = onRequest({ cors: true, maxInstances: 1, concurrency: 80 }, async (req, res) => {
  if (req.method !== 'POST') {
    return res.status(405).send('Method Not Allowed');
  }

  const { firebaseUid, licenseId } = req.body;

  if (!firebaseUid || !licenseId) {
    return res.status(400).send('Missing required fields');
  }

  try {
    // 1. Verify the license exists and is active in Firestore
    const licenseDoc = await getAdmin().firestore().collection("users").doc(firebaseUid).collection("licenses").doc(licenseId).get();
    
    if (!licenseDoc.exists || !licenseDoc.data().active) {
      return res.status(403).send('License not found or inactive');
    }

    const licenseData = licenseDoc.data();
    
    // 2. Load Enterprise Private Key (from Env or Local File)
    let privateKeyPem;
    try {
      privateKeyPem = process.env.LICENSE_PRIVATE_KEY || fs.readFileSync('./enterprise_private.pem', 'utf8');
    } catch (e) {
      logger.error("Missing private key:", e);
      return res.status(500).send("Critical Error: Enterprise Private Key not configured.");
    }

    // 3. Construct the exact payload string to sign
    const payload = JSON.stringify({
      uid: firebaseUid,
      lid: licenseId,
      pid: licenseData.productId,
      exp: licenseData.expiresAt ? licenseData.expiresAt.toDate().getTime() : "NEVER",
      iss: "Lx8Labs"
    });

    // 4. Create an ECDSA Signature (SHA256)
    const sign = crypto.createSign('SHA256');
    sign.update(payload);
    sign.end();
    const signature = sign.sign(privateKeyPem, 'base64');

    // 5. Package the final Offline License Token (Base64Url encoded payload . signature)
    const encodedPayload = Buffer.from(payload).toString('base64url');
    const encodedSignature = Buffer.from(signature, 'base64').toString('base64url');
    
    const offlineToken = `LX8-${encodedPayload}.${encodedSignature}`;

    res.json({ token: offlineToken });
  } catch (error) {
    logger.error('Offline License Generation Error:', error);
    res.status(500).json({ error: error.message });
  }
});

// 5. Global Single Sign-On (SSO) Session Cookie Generator
exports.createSessionCookie = onRequest({ cors: true, maxInstances: 1, concurrency: 80 }, async (req, res) => {
  if (req.method !== 'POST') {
    return res.status(405).send('Method Not Allowed');
  }

  const { idToken } = req.body;
  if (!idToken) {
    return res.status(400).send('Missing idToken');
  }

  try {
    // Set session expiration to 14 days
    const expiresIn = 1000 * 60 * 60 * 24 * 14;
    
    // Create the session cookie from the Firebase ID token
    const sessionCookie = await getAdmin().auth().createSessionCookie(idToken, { expiresIn });
    
    // Set the cookie securely on the root domain (.lx8labs.com)
    // In local development, we omit the domain so it works on localhost
    const isLocalhost = req.hostname === 'localhost' || req.hostname === '127.0.0.1';
    const domainOpt = isLocalhost ? '' : 'Domain=.lx8labs.com;';
    
    const options = { maxAge: expiresIn, httpOnly: true, secure: !isLocalhost };
    
    res.setHeader('Set-Cookie', `__session=${sessionCookie}; ${domainOpt} Path=/; Max-Age=${expiresIn / 1000}; HttpOnly; ${!isLocalhost ? 'Secure; SameSite=Lax;' : 'SameSite=Lax;'}`);
    res.json({ status: 'success' });
  } catch (error) {
    logger.error('SSO Cookie Generation Error:', error);
    res.status(500).json({ error: error.message });
  }
});

// 6. Client Management: Device Tracking & Registration
exports.registerClientDevice = onRequest({ cors: true, maxInstances: 1, concurrency: 80 }, async (req, res) => {
  if (req.method !== 'POST') {
    return res.status(405).send('Method Not Allowed');
  }

  const { firebaseUid, licenseId, hardwareFingerprint, osVersion } = req.body;

  if (!firebaseUid || !licenseId || !hardwareFingerprint) {
    return res.status(400).send('Missing required fields');
  }

  try {
    const licenseRef = getAdmin().firestore().collection("users").doc(firebaseUid).collection("licenses").doc(licenseId);
    const licenseDoc = await licenseRef.get();
    
    if (!licenseDoc.exists || !licenseDoc.data().active) {
      return res.status(403).send('License not found or inactive');
    }

    const devicesRef = licenseRef.collection("devices");
    
    // Run a transaction to ensure we don't exceed the device limit (e.g., max 3)
    await getAdmin().firestore().runTransaction(async (transaction) => {
      const snapshot = await transaction.get(devicesRef);
      const devices = snapshot.docs;
      
      const deviceExists = devices.find(d => d.id === hardwareFingerprint);
      
      if (!deviceExists && devices.length >= 3) {
        throw new Error('Device limit exceeded. Max 3 devices allowed per license.');
      }
      
      transaction.set(devicesRef.doc(hardwareFingerprint), {
        osVersion: osVersion || "unknown",
        lastSeen: getAdmin().firestore.FieldValue.serverTimestamp(),
        registeredAt: deviceExists ? deviceExists.data().registeredAt : getAdmin().firestore.FieldValue.serverTimestamp()
      }, { merge: true });
    });

    logger.info(`Successfully registered device ${hardwareFingerprint} for license ${licenseId}`);
    res.json({ status: 'success', deviceId: hardwareFingerprint });
  } catch (error) {
    logger.error('Device Registration Error:', error);
    res.status(400).json({ error: error.message });
  }
});

// 7. Client Management: Revoke Device
exports.revokeClientDevice = onRequest({ cors: true, maxInstances: 1, concurrency: 80 }, async (req, res) => {
  if (req.method !== 'POST') {
    return res.status(405).send('Method Not Allowed');
  }

  const { firebaseUid, licenseId, hardwareFingerprint } = req.body;

  if (!firebaseUid || !licenseId || !hardwareFingerprint) {
    return res.status(400).send('Missing required fields');
  }

  try {
    await getAdmin().firestore().collection("users").doc(firebaseUid)
      .collection("licenses").doc(licenseId)
      .collection("devices").doc(hardwareFingerprint).delete();

    logger.info(`Successfully revoked device ${hardwareFingerprint} for license ${licenseId}`);
    res.json({ status: 'success' });
  } catch (error) {
    logger.error('Device Revocation Error:', error);
    res.status(500).json({ error: error.message });
  }
});
