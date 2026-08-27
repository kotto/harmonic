import { Component, type ReactNode, type ErrorInfo } from 'react';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

/**
 * Error Boundary — capture les erreurs React pour eviter l'ecran blanc
 * et propose un bouton de reprise.
 */
export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('[ErrorBoundary]', error, info.componentStack);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{
          display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
          minHeight: '100dvh', background: '#0e0e1a', color: '#fff', padding: 24, gap: 16,
        }}>
          <span style={{ fontSize: 48 }}>⚠️</span>
          <h1 style={{ fontSize: 18, fontWeight: 400, textAlign: 'center' }}>
            Une erreur est survenue
          </h1>
          <p style={{ fontSize: 12, color: 'rgba(255,255,255,.5)', maxWidth: 300, textAlign: 'center' }}>
            {this.state.error?.message ?? 'Erreur inconnue'}
          </p>
          <button
            onClick={() => this.setState({ hasError: false, error: null })}
            style={{
              padding: '12px 32px', borderRadius: 14, border: 'none',
              background: 'rgba(155,148,255,.22)', color: '#9b94ff',
              fontSize: 14, cursor: 'pointer', marginTop: 8,
            }}
          >
            Reessayer
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}