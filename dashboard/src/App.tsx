import { BrowserRouter as Router, Routes, Route, Link, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import Auth from './components/Auth';
import Dashboard from './pages/Dashboard';
import Support from './pages/Support';
import { ErrorBoundary } from './components/ErrorBoundary';
import './index.css';

// Home Component
function Home() {
  return (
    <div className="glass-panel" style={{ textAlign: 'center', marginTop: '4rem' }}>
      <h1 style={{ marginBottom: '1rem', fontSize: '2.5rem' }}>Welcome to LX8 Central</h1>
      <p style={{ color: 'var(--text-muted)', marginBottom: '2rem' }}>
        Manage your autonomous systems, licenses, and developer environments.
      </p>
      <div className="flex-row" style={{ justifyContent: 'center' }}>
        <Link to="/portal">
          <button className="btn-primary">Go to Client Portal</button>
        </Link>
        <button className="btn-secondary">View Documentation</button>
      </div>
    </div>
  );
}

// Protected Route Wrapper
function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { currentUser, loading } = useAuth();
  
  if (loading) return <div>Loading...</div>;
  if (!currentUser) return <Navigate to="/login" />;
  
  return <>{children}</>;
}

// Navigation Bar
function Navigation() {
  const { currentUser, logout } = useAuth();
  
  return (
    <header className="nav-header">
      <Link to="/" style={{ textDecoration: 'none' }}>
        <div className="brand">LX8 LABS</div>
      </Link>
      <nav className="flex-row">
        <Link to="/" style={{ color: 'var(--text-main)', textDecoration: 'none' }}>Home</Link>
        <Link to="/portal" style={{ color: 'var(--text-main)', textDecoration: 'none' }}>Portal</Link>
        <Link to="/support" style={{ color: 'var(--text-main)', textDecoration: 'none' }}>Support</Link>
        
        {currentUser ? (
          <button className="btn-secondary" onClick={logout} style={{ padding: '0.4rem 1rem' }}>Sign Out</button>
        ) : (
          <Link to="/login">
            <button className="btn-primary" style={{ padding: '0.4rem 1rem' }}>Sign In</button>
          </Link>
        )}
      </nav>
    </header>
  );
}

// Main App
export default function App() {
  return (
    <ErrorBoundary>
      <AuthProvider>
        <Router>
          <div className="container">
          <Navigation />
          <main>
            <Routes>
              <Route path="/" element={<Home />} />
              <Route path="/login" element={<Auth />} />
              <Route 
                path="/portal" 
                element={
                  <ProtectedRoute>
                    <Dashboard />
                  </ProtectedRoute>
                } 
              />
              <Route 
                path="/support" 
                element={
                  <ProtectedRoute>
                    <Support />
                  </ProtectedRoute>
                } 
              />
            </Routes>
          </main>
        </div>
      </Router>
    </AuthProvider>
    </ErrorBoundary>
  );
}
