import { initializeApp } from "https://www.gstatic.com/firebasejs/10.11.1/firebase-app.js";
import { getAuth, signInWithEmailAndPassword, onAuthStateChanged, signOut, GoogleAuthProvider, signInWithPopup } from "https://www.gstatic.com/firebasejs/10.11.1/firebase-auth.js";
import { getFirestore, collection, getDocs, doc, setDoc, updateDoc } from "https://www.gstatic.com/firebasejs/10.11.1/firebase-firestore.js";
import { getPerformance } from "https://www.gstatic.com/firebasejs/10.11.1/firebase-performance.js";

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
const auth = getAuth(app);
const db = getFirestore(app);
const perf = getPerformance(app);
const googleProvider = new GoogleAuthProvider();

export { auth, db, perf, signInWithEmailAndPassword, onAuthStateChanged, signOut, googleProvider, signInWithPopup, collection, getDocs, doc, setDoc, updateDoc };
