const crypto = require('crypto');
const fs = require('fs');

console.log("Generating Enterprise ECDSA Keypair for Offline Licensing...");

const { publicKey, privateKey } = crypto.generateKeyPairSync('ec', {
  namedCurve: 'prime256v1',
  publicKeyEncoding: {
    type: 'spki',
    format: 'pem'
  },
  privateKeyEncoding: {
    type: 'pkcs8',
    format: 'pem'
  }
});

fs.writeFileSync('enterprise_private.pem', privateKey);
fs.writeFileSync('enterprise_public.pem', publicKey);

console.log("Keys generated successfully!");
console.log("- enterprise_private.pem (KEEP THIS SECRET! Upload to Firebase Functions ENV)");
console.log("- enterprise_public.pem (Bundle this inside Tupã IDE and aimem CLI)");
