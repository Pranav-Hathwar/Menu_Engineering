import { Component } from 'react';
import { AlertTriangle } from 'lucide-react';

/**
 * Catches any render-time error in the subtree and shows a friendly fallback
 * instead of an unrecoverable white screen.
 */
export class ErrorBoundary extends Component {
    constructor(props) {
        super(props);
        this.state = { hasError: false, error: null };
    }

    static getDerivedStateFromError(error) {
        return { hasError: true, error };
    }

    componentDidCatch(error, info) {
        // Keep console.error so failures remain diagnosable in production.
        console.error('Render error caught by ErrorBoundary:', error, info);
    }

    handleReload = () => {
        this.setState({ hasError: false, error: null });
        window.location.assign('/');
    };

    render() {
        if (!this.state.hasError) return this.props.children;

        return (
            <div className="min-h-screen flex items-center justify-center bg-background p-6">
                <div className="max-w-md w-full bg-white rounded-lg border border-slate-200 shadow-soft p-8 text-center">
                    <div className="w-14 h-14 bg-red-50 rounded-md flex items-center justify-center mx-auto mb-5 border border-red-100">
                        <AlertTriangle className="w-7 h-7 text-red-500" />
                    </div>
                    <h1 className="text-xl font-black text-slate-900">Something went wrong</h1>
                    <p className="text-sm text-slate-500 mt-2">
                        The page hit an unexpected error. Your data is safe — try reloading the
                        dashboard.
                    </p>
                    <button
                        onClick={this.handleReload}
                        className="mt-6 px-5 py-2.5 rounded-md bg-ink-900 text-white font-semibold text-sm hover:bg-primary-700 transition-colors"
                    >
                        Reload Dashboard
                    </button>
                </div>
            </div>
        );
    }
}
