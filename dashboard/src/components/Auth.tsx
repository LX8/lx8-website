import { useState } from 'react';
import { auth, googleProvider } from '../firebase';
import { createUserWithEmailAndPassword, signInWithEmailAndPassword, signInWithPopup, User } from 'firebase/auth';
import { useNavigate } from 'react-router-dom';

const triggerSSOCookie = async (user: User) => {
  try {
    const idToken = await user.getIdToken();
    await fetch('https://us-central1-lx8-labs-website.cloudfunctions.net/createSessionCookie', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ idToken })
    });
  } catch (err) {
    console.error('SSO Cookie Error:', err);
  }
};

export default function Auth() {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleAuth = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    try {
      let userCredential;
      if (isLogin) {
        userCredential = await signInWithEmailAndPassword(auth, email, password);
      } else {
        userCredential = await createUserWithEmailAndPassword(auth, email, password);
      }
      await triggerSSOCookie(userCredential.user);
      navigate('/portal');
    } catch (err: any) {
      setError(err.message);
    }
  };

  const handleGoogle = async () => {
    try {
      const result = await signInWithPopup(auth, googleProvider);
      await triggerSSOCookie(result.user);
      navigate('/portal');
    } catch (err: any) {
      setError(err.message);
    }
  };

  return (
    <div className="glass-panel" style={{ maxWidth: '400px', margin: '4rem auto', textAlign: 'center' }}>
      <h2 style={{ marginBottom: '1.5rem' }}>{isLogin ? 'Sign In' : 'Create Account'}</h2>
      {error && <p style={{ color: '#ff5252', fontSize: '0.9rem', marginBottom: '1rem' }}>{error}</p>}
      
      <form onSubmit={handleAuth} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        <input 
          type="email" 
          placeholder="Email Address" 
          value={email} 
          onChange={(e) => setEmail(e.target.value)}
          required
          style={{ padding: '0.8rem', borderRadius: '8px', border: '1px solid var(--glass-border)', background: 'rgba(0,0,0,0.5)', color: '#fff' }}
        />
        <input 
          type="password" 
          placeholder="Password" 
          value={password} 
          onChange={(e) => setPassword(e.target.value)}
          required
          style={{ padding: '0.8rem', borderRadius: '8px', border: '1px solid var(--glass-border)', background: 'rgba(0,0,0,0.5)', color: '#fff' }}
        />
        <button type="submit" className="btn-primary">{isLogin ? 'Sign In' : 'Register'}</button>
      </form>

      <div style={{ margin: '1.5rem 0', color: 'var(--text-muted)' }}>OR</div>
      
      <button onClick={handleGoogle} className="btn-secondary" style={{ width: '100%' }}>
        Continue with Google
      </button>

      <p style={{ marginTop: '1.5rem', fontSize: '0.9rem', color: 'var(--text-muted)' }}>
        {isLogin ? "Don't have an account? " : "Already have an account? "}
        <span onClick={() => setIsLogin(!isLogin)} style={{ color: 'var(--accent-cyan)', cursor: 'pointer' }}>
          {isLogin ? 'Register' : 'Sign In'}
        </span>
      </p>
    </div>
  );
}
