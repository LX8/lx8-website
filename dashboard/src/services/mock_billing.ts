import { db } from '../firebase';
import { doc, setDoc, collection, query, where, getDocs } from 'firebase/firestore';

export interface Purchase {
  productId: string;
  gateway: 'polar' | 'lemonsqueezy';
  status: 'active' | 'expired';
  purchasedAt: string;
  expiresAt: string | null;
}

export interface License {
  licenseKey: string;
  ownerId: string;
  email: string;
  status: 'valid' | 'expired' | 'revoked';
  productId: string;
  activatedDevices: string[];
  maxDevices: number;
  createdAt: string;
}

// Generate an Ed25519-like mock cryptographically verifiable license key for Tupã
export function generateLicenseKey(productId: string): string {
  const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
  let segment = '';
  for (let i = 0; i < 4; i++) {
    let part = '';
    for (let j = 0; j < 4; j++) {
      part += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    segment += (segment ? '-' : '') + part;
  }
  return `LX8-${productId.replace('prod_', '').toUpperCase().substring(0, 4)}-${segment}`;
}

// Simulate secure Webhook processing (Polar.sh / LemonSqueezy)
export async function simulatePurchaseWebhook(uid: string, email: string, productId: string) {
  const timestamp = new Date().toISOString();
  
  // 1. Write purchase to user's collection
  const purchaseRef = doc(db, 'users', uid, 'purchases', productId);
  const purchaseData: Purchase = {
    productId,
    gateway: productId === 'prod_tupa_ide' ? 'lemonsqueezy' : 'polar',
    status: 'active',
    purchasedAt: timestamp,
    expiresAt: null
  };
  await setDoc(purchaseRef, purchaseData);

  // 2. If it is Tupã IDE, create a license key
  if (productId === 'prod_tupa_ide') {
    const licenseKey = generateLicenseKey('tupa_ide');
    const licenseRef = doc(db, 'licenses', licenseKey);
    const licenseData: License = {
      licenseKey,
      ownerId: uid,
      email,
      status: 'valid',
      productId: 'lx8-tupa-ide',
      activatedDevices: [],
      maxDevices: 3,
      createdAt: timestamp
    };
    await setDoc(licenseRef, licenseData);
  }

  // 3. If it is aimem, create a mock cryptographic local-first license certificate
  if (productId === 'prod_aimem') {
    const licenseKey = generateLicenseKey('aimem');
    const licenseRef = doc(db, 'licenses', licenseKey);
    const licenseData: License = {
      licenseKey,
      ownerId: uid,
      email,
      status: 'valid',
      productId: 'lx8-aimem',
      activatedDevices: ['local-mcp-server'],
      maxDevices: 1,
      createdAt: timestamp
    };
    await setDoc(licenseRef, licenseData);
  }
}

// Load all active user purchases from Firestore
export async function fetchUserPurchases(uid: string): Promise<Purchase[]> {
  try {
    const purchasesRef = collection(db, 'users', uid, 'purchases');
    const snap = await getDocs(purchasesRef);
    const list: Purchase[] = [];
    snap.forEach((docSnap) => {
      list.push(docSnap.data() as Purchase);
    });
    return list;
  } catch (err) {
    console.error('Error fetching purchases', err);
    return [];
  }
}

// Load all active user software licenses from Firestore
export async function fetchUserLicenses(uid: string): Promise<License[]> {
  try {
    const licensesRef = collection(db, 'licenses');
    const q = query(licensesRef, where('ownerId', '==', uid));
    const snap = await getDocs(q);
    const list: License[] = [];
    snap.forEach((docSnap) => {
      list.push(docSnap.data() as License);
    });
    return list;
  } catch (err) {
    console.error('Error fetching licenses', err);
    return [];
  }
}
