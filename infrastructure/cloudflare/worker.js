/**
 * Lx8 Labs Hyperscale Telemetry Worker
 * 
 * Captures millions of telemetry/device pings at the edge, buffers them
 * into memory, and flushes them to Google Cloud Pub/Sub every 10 seconds
 * to achieve extreme cost-efficiency.
 */

let buffer = [];
let isFlushing = false;

export default {
  async fetch(request, env, ctx) {
    if (request.method !== 'POST') {
      return new Response('Method Not Allowed', { status: 405 });
    }

    try {
      const body = await request.json();
      
      // Add geographical metadata from Cloudflare Edge
      const payload = {
        ...body,
        cfRay: request.headers.get('cf-ray'),
        country: request.cf?.country,
        colo: request.cf?.colo,
        timestamp: Date.now()
      };

      // Push to in-memory buffer
      buffer.push(payload);

      // Trigger asynchronous flush if buffer gets large or time elapses
      if (buffer.length >= 1000 && !isFlushing) {
        ctx.waitUntil(flushToPubSub(env));
      }

      return new Response('Buffered', { status: 202 });
    } catch (e) {
      return new Response('Bad Request', { status: 400 });
    }
  },

  // Cron trigger to ensure we never drop events even if traffic slows
  async scheduled(event, env, ctx) {
    if (buffer.length > 0 && !isFlushing) {
      ctx.waitUntil(flushToPubSub(env));
    }
  }
};

async function flushToPubSub(env) {
  isFlushing = true;
  const currentBatch = [...buffer];
  buffer = []; // Reset buffer instantly for incoming traffic

  if (currentBatch.length === 0) {
    isFlushing = false;
    return;
  }

  try {
    // Standard GCP Pub/Sub REST API POST
    const pubsubUrl = `https://pubsub.googleapis.com/v1/projects/${env.GCP_PROJECT_ID}/topics/${env.PUBSUB_TOPIC}:publish`;
    
    // Format for Pub/Sub (Base64 encoded data)
    const messages = currentBatch.map(msg => ({
      data: btoa(JSON.stringify(msg))
    }));

    await fetch(pubsubUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${env.GCP_SERVICE_ACCOUNT_TOKEN}` // Requires edge KV or short-lived JWT strategy
      },
      body: JSON.stringify({ messages })
    });

  } catch (error) {
    // If flush fails, push back to buffer to retry
    buffer = [...currentBatch, ...buffer];
    console.error("Flush failed, retrying later.", error);
  } finally {
    isFlushing = false;
  }
}
