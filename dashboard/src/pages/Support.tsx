import { useState, useEffect } from 'react';
import { db } from '../firebase';
import { collection, addDoc, query, orderBy, onSnapshot, serverTimestamp } from 'firebase/firestore';
import { useAuth } from '../contexts/AuthContext';

export default function Support() {
  const { currentUser } = useAuth();
  const [message, setMessage] = useState('');
  const [tickets, setTickets] = useState<any[]>([]);

  useEffect(() => {
    if (!currentUser) return;
    const q = query(collection(db, 'users', currentUser.uid, 'support'), orderBy('createdAt', 'desc'));
    const unsubscribe = onSnapshot(q, (snapshot) => {
      setTickets(snapshot.docs.map(doc => ({ id: doc.id, ...doc.data() })));
    });
    return unsubscribe;
  }, [currentUser]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!message.trim() || !currentUser) return;

    const ticketContent = message;
    setMessage('');

    await addDoc(collection(db, 'users', currentUser.uid, 'support'), {
      content: ticketContent,
      sender: 'user',
      createdAt: serverTimestamp(),
      status: 'OPEN'
    });
  };

  return (
    <div className="glass-panel" style={{ maxWidth: '800px', margin: '2rem auto' }}>
      <h2>AI Triage Support</h2>
      <p style={{ color: 'var(--text-muted)', marginBottom: '2rem' }}>
        Submit your infrastructure or licensing issues. Our Antigravity L1 Agent will automatically analyze and resolve basic issues.
      </p>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', marginBottom: '2rem', maxHeight: '400px', overflowY: 'auto', padding: '1rem', background: 'rgba(0,0,0,0.2)', borderRadius: '8px' }}>
        {tickets.length === 0 ? <p style={{ textAlign: 'center', color: 'var(--text-muted)' }}>No support history.</p> : null}
        
        {tickets.map(ticket => (
          <div key={ticket.id} style={{ 
            padding: '1rem', 
            borderRadius: '8px', 
            background: ticket.sender === 'agent' ? 'rgba(102, 252, 241, 0.1)' : 'rgba(255,255,255,0.05)',
            borderLeft: ticket.sender === 'agent' ? '4px solid var(--primary)' : '4px solid transparent',
            marginLeft: ticket.sender === 'user' ? '2rem' : '0',
            marginRight: ticket.sender === 'agent' ? '2rem' : '0'
          }}>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.5rem', textTransform: 'uppercase' }}>
              {ticket.sender === 'agent' ? '🤖 Antigravity Agent' : 'You'}
            </div>
            <div style={{ whiteSpace: 'pre-wrap', lineHeight: '1.5' }}>{ticket.content}</div>
            
            {ticket.status === 'RESOLVED' && (
              <span className="badge" style={{ marginTop: '0.5rem', display: 'inline-block', background: 'rgba(74,222,128,0.2)', color: '#4ade80' }}>RESOLVED</span>
            )}
          </div>
        ))}
      </div>

      <form onSubmit={handleSubmit} style={{ display: 'flex', gap: '1rem' }}>
        <textarea 
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder="Describe your issue..."
          style={{ flex: 1, padding: '1rem', borderRadius: '8px', border: '1px solid var(--surface-border)', background: 'rgba(0,0,0,0.5)', color: '#fff', minHeight: '80px', resize: 'vertical' }}
        />
        <button type="submit" className="btn-primary" style={{ alignSelf: 'flex-end', padding: '1rem 2rem' }}>
          Submit Ticket
        </button>
      </form>
    </div>
  );
}
