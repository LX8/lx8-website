import { initializeApp } from "firebase/app";
import { getAuth, GoogleAuthProvider } from "firebase/auth";
import { getFirestore } from "firebase/firestore";

const firebaseConfig = {
  projectId: "lx8-labs-website",
  appId: "1:627672853515:web:661a6d0746517d05b1ab0e",
  storageBucket: "lx8-labs-website.firebasestorage.app",
  apiKey: "AIzaSyDckhJc4oWNClLJYem1UASwx7q0gTLhoV8",
  authDomain: "lx8-labs-website.firebaseapp.com",
  messagingSenderId: "627672853515",
  measurementId: "G-WM2YC9T8SB"
};

const app = initializeApp(firebaseConfig);
export const auth = getAuth(app);
export const db = getFirestore(app);
export const googleProvider = new GoogleAuthProvider();
