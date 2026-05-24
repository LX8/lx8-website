import React from 'react';
import { getAnalytics, logEvent } from 'firebase/analytics';

interface State {
  hasError: boolean;
  error?: Error;
}

export class ErrorBoundary extends React.Component<{ children: React.ReactNode }, State> {
  constructor(props: { children: React.ReactNode }) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error("Crashlytics Web Caught:", error, errorInfo);
    try {
      const analytics = getAnalytics();
      logEvent(analytics, 'exception', {
        description: error.message,
        fatal: true,
      });
    } catch (e) {
      // Ignore analytics failures
    }
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{ padding: '2rem', textAlign: 'center', marginTop: '10vh' }}>
          <h2>UI Render Failure</h2>
          <p style={{ color: 'var(--text-muted)' }}>The telemetry agent has logged this fatal exception.</p>
          <pre style={{ color: '#ff5252', background: 'rgba(0,0,0,0.5)', padding: '1rem', display: 'inline-block', textAlign: 'left', marginTop: '1rem' }}>
            {this.state.error?.message}
          </pre>
          <br/>
          <button onClick={() => window.location.reload()} style={{ marginTop: '1rem' }}>Reload Application</button>
        </div>
      );
    }
    return this.props.children;
  }
}
