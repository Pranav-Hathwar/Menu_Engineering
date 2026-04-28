import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { PieChart, ShieldCheck } from 'lucide-react';

import { useAuth } from '../hooks/useAuth';
import { Button } from '../ui/Button';
import { Card } from '../ui/Card';
import { Input } from '../ui/Input';

export default function Login() {
    const { login } = useAuth();
    const navigate = useNavigate();
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState(null);
    const [loading, setLoading] = useState(false);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError(null);
        try {
            await login(email, password);
            navigate('/');
        } catch (err) {
            setError(err.message || "Invalid credentials. Check your email and password.");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-background grid grid-cols-1 lg:grid-cols-[1.05fr_0.95fr]">
            <section className="relative hidden lg:block overflow-hidden">
                <div
                    className="absolute inset-0 bg-cover bg-center"
                    style={{ backgroundImage: "url('https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?auto=format&fit=crop&w=1600&q=80')" }}
                />
                <div className="absolute inset-0 bg-gradient-to-br from-ink-900/95 via-ink-900/70 to-primary-700/45" />
                <div className="relative h-full p-12 flex flex-col justify-between text-white">
                    <div className="flex items-center gap-3">
                        <div className="w-11 h-11 bg-white/10 border border-white/20 rounded-md flex items-center justify-center">
                            <PieChart className="w-6 h-6 text-primary-100" />
                        </div>
                        <div>
                            <p className="font-black text-xl tracking-tight">MenuMind Pro</p>
                            <p className="text-xs text-white/60 uppercase tracking-widest">Restaurant intelligence</p>
                        </div>
                    </div>
                    <div className="max-w-xl">
                        <p className="text-xs font-bold uppercase tracking-[0.28em] text-primary-100">From messy sales files to decisions</p>
                        <h1 className="text-5xl font-black tracking-tight mt-4 leading-tight">Turn menu data into margin strategy.</h1>
                        <p className="text-white/72 mt-5 text-base leading-relaxed">
                            Upload real POS exports, normalize the chaos, and see revenue drivers, weak margins, and menu-engineering moves in one workspace.
                        </p>
                    </div>
                    <div className="flex items-center gap-3 text-sm text-white/70">
                        <ShieldCheck className="w-5 h-5 text-primary-100" />
                        Authenticated workspace with owner-scoped analytics.
                    </div>
                </div>
            </section>

            <main className="flex items-center justify-center p-5 sm:p-8 surface-grid">
                <motion.div
                    initial={{ opacity: 0, scale: 0.97 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ duration: 0.45, ease: "easeOut" }}
                    className="w-full max-w-md"
                >
                    <div className="flex flex-col items-center mb-8 lg:hidden">
                        <div className="w-14 h-14 bg-ink-900 rounded-lg shadow-sm flex items-center justify-center mb-4">
                            <PieChart className="w-8 h-8 text-primary-100" />
                        </div>
                        <h1 className="text-2xl font-black text-slate-900 tracking-tight">MenuMind Pro</h1>
                        <p className="text-slate-500 text-sm mt-1">Restaurant intelligence workspace.</p>
                    </div>

                    <Card className="p-8 border-slate-200" hover={false}>
                        <div className="mb-7">
                            <p className="text-xs font-bold uppercase tracking-[0.22em] text-primary-700">Secure sign in</p>
                            <h2 className="text-2xl font-black text-slate-900 mt-2">Welcome back</h2>
                        </div>
                        <form onSubmit={handleSubmit} className="space-y-5">
                            <Input
                                label="Email Address"
                                type="email"
                                placeholder="owner@restaurant.com"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                required
                            />
                            <Input
                                label="Password"
                                type="password"
                                placeholder="Enter your password"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                required
                            />

                            {error && <p className="text-red-600 text-sm font-semibold">{error}</p>}

                            <Button type="submit" className="w-full py-2.5 mt-2" disabled={loading}>
                                {loading ? 'Authenticating...' : 'Sign In'}
                            </Button>
                            <p className="text-sm text-slate-500 text-center">
                                New here? <Link to="/signup" className="font-bold text-primary-700 hover:underline">Create an account</Link>
                            </p>
                        </form>
                    </Card>
                </motion.div>
            </main>
        </div>
    );
}
