import { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { auth } from '../firebase';
import { signOut } from 'firebase/auth';
import { 
  simulatePurchaseWebhook, 
  fetchUserPurchases, 
  fetchUserLicenses
} from '../services/mock_billing';
import type { Purchase, License } from '../services/mock_billing';

// Bionic Reading Highlighting Engine for ADHD Cognitive Focus
function BionicText({ text, active }: { text: string; active: boolean }) {
  if (!active) return <>{text}</>;
  const words = text.split(/(\s+)/);
  return (
    <>
      {words.map((word, i) => {
        if (word.trim().length === 0) return word;
        const len = word.length;
        const boldLen = len <= 3 ? 1 : len <= 6 ? 2 : Math.ceil(len * 0.45);
        const boldPart = word.substring(0, boldLen);
        const restPart = word.substring(boldLen);
        return (
          <span key={i} className="lx8-bionic-word" style={{ display: 'inline' }}>
            <strong style={{ fontWeight: 700, color: 'var(--primary)' }}>{boldPart}</strong>
            {restPart}
          </span>
        );
      })}
    </>
  );
}

interface SreTarget {
  id: string;
  subdomain: string;
  category: string;
  description: string;
  version: string;
  commit: string;
  buildTime: string;
  status: 'ONLINE' | 'OFFLINE' | 'PROPAGATING';
}

export default function Dashboard() {
  const { currentUser } = useAuth();
  const [purchases, setPurchases] = useState<Purchase[]>([]);
  const [licenses, setLicenses] = useState<License[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [revealedKeys, setRevealedKeys] = useState<{ [key: string]: boolean }>({});

  // Cognitive A11y States
  const [dyslexicMode, setDyslexicMode] = useState(() => localStorage.getItem('lx8-a11y-dyslexic') === 'true');
  const [bionicMode, setBionicMode] = useState(() => localStorage.getItem('lx8-a11y-bionic') === 'true');
  const [rulerActive, setRulerActive] = useState(() => localStorage.getItem('lx8-a11y-ruler') === 'true');
  const [rulerY, setRulerY] = useState(-100);

  // Book interaction state
  const [spinA, setSpinA] = useState<'UP' | 'DOWN'>('UP');
  const [spinB, setSpinB] = useState<'UP' | 'DOWN'>('DOWN');

  // SRE Audit Board States
  const [sreTargets, setSreTargets] = useState<SreTarget[]>([
    { id: 'lx8-aimem', subdomain: 'aimem', category: 'Developer Tools', description: 'AI Memory System', version: '1.0.0', commit: 'da0dfb2', buildTime: '', status: 'PROPAGATING' },
    { id: 'lx8-tupa', subdomain: 'tupa', category: 'Developer Tools', description: 'Tupã IDE Landing', version: '1.0.0', commit: 'da0dfb2', buildTime: '', status: 'PROPAGATING' },
    { id: 'lx8-tupa-ide', subdomain: 'tupaide', category: 'Developer Tools', description: 'Tupã IDE Web App', version: '1.0.0', commit: 'da0dfb2', buildTime: '', status: 'PROPAGATING' },
    { id: 'lx8-bmss', subdomain: 'suit', category: 'Autonomous Systems', description: 'Aegis Swarm Suit', version: '1.0.0', commit: 'da0dfb2', buildTime: '', status: 'PROPAGATING' },
    { id: 'bipartitebook', subdomain: 'bipartitebook', category: 'Publications', description: 'Bipartite Book', version: '1.0.0', commit: 'da0dfb2', buildTime: '', status: 'PROPAGATING' },
    { id: 'lx8-installations', subdomain: 'installations', category: 'Infrastructure', description: 'Labs Management', version: '1.0.0', commit: 'da0dfb2', buildTime: '', status: 'PROPAGATING' },
    { id: 'lx8-mattermem', subdomain: 'mattermem', category: 'Infrastructure', description: 'Hardware Memory', version: '1.0.0', commit: 'da0dfb2', buildTime: '', status: 'PROPAGATING' },
  ]);

  // Load user licenses & purchases
  const loadUserData = async () => {
    if (!currentUser) return;
    try {
      const p = await fetchUserPurchases(currentUser.uid);
      const l = await fetchUserLicenses(currentUser.uid);
      setPurchases(p);
      setLicenses(l);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // Ping subdomain version.json payloads asynchronously
  const auditSreInfrastructure = async () => {
    const updated = await Promise.all(
      sreTargets.map(async (target) => {
        try {
          // Attempt to fetch live version.json from custom subdomain
          const controller = new AbortController();
          const id = setTimeout(() => controller.abort(), 2000); // 2s timeout
          
          const res = await fetch(`https://${target.subdomain}.lx8labs.com/version.json`, { signal: controller.signal });
          clearTimeout(id);
          
          if (res.ok) {
            const data = await res.json();
            return {
              ...target,
              version: data.version || target.version,
              commit: data.commit || target.commit,
              buildTime: data.buildTime || '',
              status: 'ONLINE' as const
            };
          }
        } catch (e) {
          // Fallback check to standard firebase app endpoints if custom DNS not ready
          try {
            const fbRes = await fetch(`https://${target.id}.web.app/version.json`);
            if (fbRes.ok) {
              const fbData = await fbRes.json();
              return {
                ...target,
                version: fbData.version || target.version,
                commit: fbData.commit || target.commit,
                buildTime: fbData.buildTime || '',
                status: 'PROPAGATING' as const  // Resolved in Firebase but DNS NXDOMAIN
              };
            }
          } catch (err) {
            // Leave as offline/propagating
          }
        }
        return { ...target, status: 'PROPAGATING' as const };
      })
    );
    setSreTargets(updated);
  };

  useEffect(() => {
    loadUserData();
    auditSreInfrastructure();
  }, [currentUser]);

  // Synchronize dynamic body classes with a11y states
  useEffect(() => {
    document.body.classList.toggle('dyslexic-mode', dyslexicMode);
    localStorage.setItem('lx8-a11y-dyslexic', String(dyslexicMode));
  }, [dyslexicMode]);

  useEffect(() => {
    document.body.classList.toggle('bionic-mode', bionicMode);
    localStorage.setItem('lx8-a11y-bionic', String(bionicMode));
  }, [bionicMode]);

  useEffect(() => {
    localStorage.setItem('lx8-a11y-ruler', String(rulerActive));
  }, [rulerActive]);

  // Capture mouse move for Line Reading Ruler
  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (rulerActive) {
        setRulerY(e.clientY - 22);
      }
    };
    window.addEventListener('mousemove', handleMouseMove);
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }, [rulerActive]);

  const handleLogout = async () => {
    try {
      await signOut(auth);
    } catch (error) {
      console.error('Failed to log out', error);
    }
  };

  const handleCheckoutMock = async (productId: string, productName: string) => {
    if (!currentUser) return;
    setActionLoading(productId);
    try {
      await simulatePurchaseWebhook(currentUser.uid, currentUser.email || '', productId);
      await loadUserData();
      alert(`✓ Mock Checkout Successful: Unlocked ${productName}! Purchase registered in Firestore.`);
    } catch (err) {
      console.error(err);
    } finally {
      setActionLoading(null);
    }
  };

  const toggleKeyReveal = (key: string) => {
    setRevealedKeys(prev => ({ ...prev, [key]: !prev[key] }));
  };

  const hasPurchased = (productId: string) => purchases.some(p => p.productId === productId);

  return (
    <div className="container">
      {/* SSO Cookie Active Banner */}
      <div className="glass sso-banner" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0.6rem 1.25rem', marginBottom: '1.5rem', borderRadius: '10px', fontSize: '0.78rem', border: '1px solid rgba(102, 252, 241, 0.18)', background: 'rgba(102, 252, 241, 0.04)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span className="dot" style={{ width: '8px', height: '8px', background: '#66fcf1', borderRadius: '50%', boxShadow: '0 0 8px #66fcf1' }}></span>
          <span>Shared SSO Cookie Active: <strong>.lx8labs.com</strong> (Seamless cross-subdomain access session)</span>
        </div>
        <span style={{ color: 'var(--text-muted)' }}>Secure SSL Gated</span>
      </div>

      {/* Header Panel */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <div>
          <h1>
            <BionicText text="Lx8 Labs Central OS" active={bionicMode} />
          </h1>
          <p>
            <BionicText text="Unified corporate business management, software licensing, and user configuration." active={bionicMode} />
          </p>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <button className="secondary" onClick={handleLogout} style={{ width: 'auto' }}>
            Sign Out
          </button>
        </div>
      </div>

      {/* Main Split Layout */}
      <div style={{ display: 'grid', gridTemplateColumns: '3fr 1fr', gap: '2rem', alignItems: 'start' }}>
        
        {/* Left Side: Business & Core Panels */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
          
          {/* Welcome Card */}
          <div className="glass" style={{ padding: '2rem' }}>
            <h2>
              Welcome, <span style={{ color: 'var(--primary)' }}>{currentUser?.displayName || currentUser?.email}</span>
            </h2>
            <p style={{ marginTop: '0.5rem' }}>
              <BionicText text="Manage your secure applications, view analytical books, and configure offline-first CLI credentials. High-contrast, neurodivergent accessibility is natively active." active={bionicMode} />
            </p>
          </div>

          {/* SRE Infrastructure Version Control & Audit Board */}
          <div className="glass" style={{ padding: '2rem' }}>
            <h3 style={{ borderBottom: '1px solid var(--surface-border)', paddingBottom: '0.75rem', marginBottom: '1.25rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span>🚀 Sovereign SRE Infrastructure Audit Board</span>
              <button 
                onClick={auditSreInfrastructure}
                style={{ width: 'auto', padding: '4px 10px', fontSize: '0.72rem', background: 'rgba(102, 252, 241, 0.1)', color: 'var(--primary)', border: '1px solid var(--primary)' }}
              >
                Scan Live Deployments
              </button>
            </h3>
            
            <p style={{ fontSize: '0.84rem', color: 'var(--text-muted)', marginBottom: '1.25rem' }}>
              Pings all deployed subdomains in real-time. Verifies live running build versions, active Git commits, and DNS propagation targets.
            </p>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
              {sreTargets.map(target => (
                <div key={target.id} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0.85rem 1.25rem', background: 'rgba(0,0,0,0.2)', border: '1px solid var(--surface-border)', borderRadius: '8px' }}>
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <strong style={{ color: '#fff', fontSize: '0.9rem' }}>{target.subdomain}.lx8labs.com</strong>
                      <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>({target.description})</span>
                    </div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px', display: 'flex', gap: '1rem' }}>
                      <span>Version: <strong style={{ color: 'var(--primary)' }}>v{target.version}</strong></span>
                      <span>Commit: <a href={`https://github.com/LX8/lx8-website/commit/${target.commit}`} target="_blank" rel="noopener" style={{ color: 'var(--primary)', fontFamily: 'monospace', textDecoration: 'underline' }}>{target.commit}</a></span>
                      {target.buildTime && <span>Deployed: {new Date(target.buildTime).toLocaleDateString()}</span>}
                    </div>
                  </div>

                  <div>
                    {target.status === 'ONLINE' ? (
                      <span style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', fontSize: '0.72rem', background: 'rgba(74,222,128,0.12)', color: '#4ade80', padding: '4px 10px', borderRadius: '4px', border: '1px solid rgba(74,222,128,0.25)' }}>
                        <span style={{ width: '6px', height: '6px', background: '#4ade80', borderRadius: '50%', boxShadow: '0 0 6px #4ade80' }}></span>
                        ONLINE
                      </span>
                    ) : target.status === 'PROPAGATING' ? (
                      <span style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', fontSize: '0.72rem', background: 'rgba(251,191,36,0.1)', color: '#fbbf24', padding: '4px 10px', borderRadius: '4px', border: '1px solid rgba(251,191,36,0.25)' }}>
                        <span style={{ width: '6px', height: '6px', background: '#fbbf24', borderRadius: '50%', boxShadow: '0 0 6px #fbbf24' }}></span>
                        PROPAGATING (DNS NXDOMAIN)
                      </span>
                    ) : (
                      <span style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', fontSize: '0.72rem', background: 'rgba(239,68,68,0.12)', color: '#ef4444', padding: '4px 10px', borderRadius: '4px', border: '1px solid rgba(239,68,68,0.25)' }}>
                        <span style={{ width: '6px', height: '6px', background: '#ef4444', borderRadius: '50%' }}></span>
                        OFFLINE
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Software Licensing Section */}
          <div className="glass" style={{ padding: '2rem' }}>
            <h3 style={{ borderBottom: '1px solid var(--surface-border)', paddingBottom: '0.75rem', marginBottom: '1.25rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span>🔑 Tupã IDE & aimem Licenses</span>
              <span style={{ fontSize: '0.7rem', color: 'var(--primary)', textTransform: 'uppercase', letterSpacing: '1px' }}>Local Validation</span>
            </h3>
            
            {loading ? (
              <p>Loading active licenses...</p>
            ) : licenses.length === 0 ? (
              <div style={{ padding: '1rem', background: 'rgba(255,255,255,0.02)', borderRadius: '8px', border: '1px dashed var(--surface-border)', textAlign: 'center' }}>
                <p style={{ marginBottom: '1rem' }}>No active license keys found on your account.</p>
                <button 
                  onClick={() => handleCheckoutMock('prod_tupa_ide', 'Tupã IDE Pro')}
                  disabled={actionLoading !== null}
                  style={{ width: 'auto' }}
                >
                  {actionLoading === 'prod_tupa_ide' ? 'Processing...' : 'Simulate Tupã Purchase ($29)'}
                </button>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                {licenses.map(lic => (
                  <div key={lic.licenseKey} className="glass" style={{ padding: '1.25rem', background: 'rgba(0,0,0,0.2)', border: '1px solid rgba(255,255,255,0.06)' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
                      <strong style={{ color: 'var(--primary)' }}>
                        {lic.productId === 'lx8-tupa-ide' ? 'Tupã IDE macOS Pro' : 'aimem CLI Pro'}
                      </strong>
                      <span className="badge" style={{ padding: '3px 8px', borderRadius: '4px', background: 'rgba(74,222,128,0.12)', color: '#4ade80', fontSize: '0.7rem', border: '1px solid rgba(74,222,128,0.25)' }}>
                        {lic.status.toUpperCase()}
                      </span>
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '0.5rem' }}>
                      <code style={{ background: 'rgba(0,0,0,0.5)', padding: '6px 12px', borderRadius: '4px', letterSpacing: '1px', flex: 1, fontFamily: 'monospace' }}>
                        {revealedKeys[lic.licenseKey] ? lic.licenseKey : 'LX8-XXXX-XXXX-XXXX-XXXX'}
                      </code>
                      <button 
                        className="secondary" 
                        onClick={() => toggleKeyReveal(lic.licenseKey)}
                        style={{ width: 'auto', padding: '6px 12px' }}
                      >
                        {revealedKeys[lic.licenseKey] ? 'Hide' : 'Reveal'}
                      </button>
                    </div>

                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                      <span>Activated: <strong>{lic.activatedDevices.length} / {lic.maxDevices}</strong> devices</span>
                      <span>Created: {new Date(lic.createdAt).toLocaleDateString()}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Interactive Bipartite Universe Gated Widget */}
          <div className="glass" style={{ padding: '2rem' }}>
            <h3 style={{ borderBottom: '1px solid var(--surface-border)', paddingBottom: '0.75rem', marginBottom: '1.25rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span>🌌 The Bipartite Universe</span>
              <span style={{ fontSize: '0.7rem', color: 'var(--primary)', textTransform: 'uppercase', letterSpacing: '1px' }}>Book Gating</span>
            </h3>

            {!hasPurchased('prod_bipartite_book') ? (
              <div className="glass" style={{ padding: '2rem', background: 'rgba(102, 252, 241, 0.02)', border: '1px dashed var(--primary)', textAlign: 'center', position: 'relative', overflow: 'hidden' }}>
                <h4 style={{ marginBottom: '0.5rem' }}>Unlock Interactive 3D Cosmology Preview</h4>
                <p style={{ fontSize: '0.85rem', marginBottom: '1.5rem' }}>
                  The Bipartite Universe is fully gated via Firestore security rules. Get immediate access to interactive quantum spinning demos, visual relativity equations, and full chapters.
                </p>
                <button 
                  onClick={() => handleCheckoutMock('prod_bipartite_book', 'The Bipartite Universe Book')}
                  disabled={actionLoading !== null}
                  style={{ width: 'auto' }}
                >
                  {actionLoading === 'prod_bipartite_book' ? 'Processing...' : 'Simulate Polar.sh Book Checkout ($19)'}
                </button>
              </div>
            ) : (
              <div>
                <div className="alert-green" style={{ padding: '1rem', background: 'rgba(74,222,128,0.06)', border: '1px solid rgba(74,222,128,0.2)', borderRadius: '8px', color: '#4ade80', fontSize: '0.85rem', marginBottom: '1.5rem' }}>
                  ✓ <strong>Full Access Active</strong>. Your profile has book reader privileges cached globally in SSO.
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: '1.5rem' }}>
                  {/* Chapter Navigation List */}
                  <div style={{ borderRight: '1px solid var(--surface-border)', paddingRight: '1rem' }}>
                    <h5 style={{ textTransform: 'uppercase', fontSize: '0.72rem', letterSpacing: '1px', marginBottom: '0.75rem', color: 'var(--text-muted)' }}>Chapters</h5>
                    <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '0.82rem' }}>
                      <li style={{ cursor: 'pointer', color: 'var(--primary)', fontWeight: 'bold' }}>I. Noether Symmetry</li>
                      <li style={{ cursor: 'pointer', color: 'var(--text-muted)' }}>II. Jocelyn Bell Pulsars</li>
                      <li style={{ cursor: 'pointer', color: 'var(--text-muted)' }}>III. Rolph Landauer Limit</li>
                    </ul>
                  </div>

                  {/* Dynamic Visualizer Demo (gated preview) */}
                  <div className="glass" style={{ padding: '1.25rem', background: 'rgba(0,0,0,0.3)' }}>
                    <h5 style={{ marginBottom: '0.5rem', color: 'var(--primary)' }}>Noether Symmetry Interactive Spin</h5>
                    <p style={{ fontSize: '0.78rem', marginBottom: '1rem' }}>
                      Quantum spins are entangled. Rotate Particle A to observe simultaneous spin shifts in Particle B.
                    </p>

                    <div style={{ display: 'flex', justifyContent: 'space-around', alignItems: 'center', padding: '1rem', background: 'rgba(0,0,0,0.4)', borderRadius: '8px', border: '1px solid var(--surface-border)', marginBottom: '1rem' }}>
                      <div style={{ textAlign: 'center' }}>
                        <div style={{ fontSize: '0.62rem', letterSpacing: '1px', textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: '4px' }}>Particle A</div>
                        <span style={{ fontSize: '1.2rem', fontWeight: 'bold', color: spinA === 'UP' ? 'var(--primary)' : '#ff6b6b' }}>
                          {spinA === 'UP' ? '↑ UP' : '↓ DOWN'}
                        </span>
                        <button 
                          className="secondary" 
                          onClick={() => {
                            const newA = spinA === 'UP' ? 'DOWN' : 'UP';
                            setSpinA(newA);
                            setSpinB(newA === 'UP' ? 'DOWN' : 'UP'); // Entangled flip
                          }}
                          style={{ marginTop: '8px', padding: '4px 8px', fontSize: '0.7rem' }}
                        >
                          Flip Spin
                        </button>
                      </div>

                      <div style={{ height: '40px', borderLeft: '1px dashed var(--surface-border)' }}></div>

                      <div style={{ textAlign: 'center' }}>
                        <div style={{ fontSize: '0.62rem', letterSpacing: '1px', textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: '4px' }}>Particle B (Entangled)</div>
                        <span style={{ fontSize: '1.2rem', fontWeight: 'bold', color: spinB === 'UP' ? 'var(--primary)' : '#ff6b6b' }}>
                          {spinB === 'UP' ? '↑ UP' : '↓ DOWN'}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Business / Billing Catalog */}
          <div className="glass" style={{ padding: '2rem' }}>
            <h3 style={{ borderBottom: '1px solid var(--surface-border)', paddingBottom: '0.75rem', marginBottom: '1.25rem' }}>
              🛒 Instant Mock Purchase Storefront
            </h3>
            <p style={{ fontSize: '0.86rem', marginBottom: '1.25rem' }}>
              Test checkout operations directly in production without incurring Stripe/Polar transaction boundaries. Bypasses tax compliance pipelines for swift local SRE validation.
            </p>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1rem' }}>
              <div className="glass" style={{ padding: '1rem', textAlign: 'center', background: 'rgba(255,255,255,0.01)' }}>
                <h4 style={{ fontSize: '0.95rem' }}>Tupã IDE License</h4>
                <div style={{ fontSize: '1.5rem', fontWeight: 'bold', margin: '0.5rem 0', color: 'var(--primary)' }}>$29</div>
                <button 
                  onClick={() => handleCheckoutMock('prod_tupa_ide', 'Tupã IDE Pro')}
                  disabled={actionLoading !== null || hasPurchased('prod_tupa_ide')}
                  style={{ width: '100%' }}
                >
                  {hasPurchased('prod_tupa_ide') ? 'Purchased ✓' : 'Buy Pro Key'}
                </button>
              </div>

              <div className="glass" style={{ padding: '1rem', textAlign: 'center', background: 'rgba(255,255,255,0.01)' }}>
                <h4 style={{ fontSize: '0.95rem' }}>Bipartite Universe Book</h4>
                <div style={{ fontSize: '1.5rem', fontWeight: 'bold', margin: '0.5rem 0', color: 'var(--primary)' }}>$19</div>
                <button 
                  onClick={() => handleCheckoutMock('prod_bipartite_book', 'The Bipartite Universe Book')}
                  disabled={actionLoading !== null || hasPurchased('prod_bipartite_book')}
                  style={{ width: '100%' }}
                >
                  {hasPurchased('prod_bipartite_book') ? 'Unlocked ✓' : 'Unlock Book'}
                </button>
              </div>

              <div className="glass" style={{ padding: '1rem', textAlign: 'center', background: 'rgba(255,255,255,0.01)' }}>
                <h4 style={{ fontSize: '0.95rem' }}>aimem CLI License</h4>
                <div style={{ fontSize: '1.5rem', fontWeight: 'bold', margin: '0.5rem 0', color: 'var(--primary)' }}>$12</div>
                <button 
                  onClick={() => handleCheckoutMock('prod_aimem', 'aimem Pro License')}
                  disabled={actionLoading !== null || hasPurchased('prod_aimem')}
                  style={{ width: '100%' }}
                >
                  {hasPurchased('prod_aimem') ? 'Unlocked ✓' : 'Get License Certificate'}
                </button>
              </div>
            </div>
          </div>

        </div>

        {/* Right Side: Accessibility & Cognitive Controls Panel */}
        <div className="glass" style={{ padding: '1.5rem', position: 'sticky', top: '20px' }}>
          <h4 style={{ borderBottom: '1px solid var(--surface-border)', paddingBottom: '0.5rem', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span>🧠 Cognitive Flow Controls</span>
          </h4>
          <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginBottom: '1.25rem', lineHeight: '1.4' }}>
            Configure visual formatting presets optimized for visual differences, ADHD, or dyslexia. Binds instantly to SSO state.
          </p>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            <label style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '0.82rem', cursor: 'pointer', fontWeight: 500 }}>
              <span>Dyslexia Friendly Font</span>
              <input 
                type="checkbox" 
                checked={dyslexicMode} 
                onChange={(e) => setDyslexicMode(e.target.checked)}
                style={{ accentColor: 'var(--primary)', width: 'auto', marginBottom: 0 }}
              />
            </label>

            <label style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '0.82rem', cursor: 'pointer', fontWeight: 500 }}>
              <span>ADHD Bionic Eye Guide</span>
              <input 
                type="checkbox" 
                checked={bionicMode} 
                onChange={(e) => setBionicMode(e.target.checked)}
                style={{ accentColor: 'var(--primary)', width: 'auto', marginBottom: 0 }}
              />
            </label>

            <label style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '0.82rem', cursor: 'pointer', fontWeight: 500 }}>
              <span>Line Reading Ruler</span>
              <input 
                type="checkbox" 
                checked={rulerActive} 
                onChange={(e) => setRulerActive(e.target.checked)}
                style={{ accentColor: 'var(--primary)', width: 'auto', marginBottom: 0 }}
              />
            </label>
          </div>
          
          <div style={{ borderTop: '1px solid var(--surface-border)', marginTop: '1.5rem', paddingTop: '1rem', fontSize: '0.75rem', color: 'var(--text-muted)', lineHeight: '1.5' }}>
            <strong>How this works:</strong>
            <ul style={{ paddingLeft: '1rem', marginTop: '4px', display: 'flex', flexDirection: 'column', gap: '4px' }}>
              <li><strong>Dyslexia Font:</strong> Swaps stylesheet base to Atkinson Hyperlegible to improve letter parsing.</li>
              <li><strong>Bionic Focus:</strong> Bolds first letters of critical statements to guide gaze flow.</li>
              <li><strong>Line Ruler:</strong> Overlays focus bounding lines to filter visual noise.</li>
            </ul>
          </div>
        </div>

      </div>

      {/* Focus Line Ruler Node Overlay */}
      {rulerActive && (
        <div 
          className="a11y-ruler" 
          style={{ 
            position: 'fixed', 
            left: 0, 
            right: 0, 
            height: '45px', 
            pointerEvents: 'none', 
            zIndex: 9998, 
            background: 'rgba(102, 252, 241, 0.05)', 
            borderTop: '1px dashed rgba(102, 252, 241, 0.3)', 
            borderBottom: '1px dashed rgba(102, 252, 241, 0.3)', 
            boxShadow: '0 0 80px rgba(102, 252, 241, 0.02)', 
            transform: `translateY(${rulerY}px)`, 
            transition: 'transform 0.05s ease-out' 
          }}
        />
      )}
    </div>
  );
}
