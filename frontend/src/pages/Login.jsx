import { useState } from 'react';
import { useAuth } from '../hooks/useAuth';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Card } from '../ui/Card';
import { Input } from '../ui/Input';
import { Button } from '../ui/Button';
import { PieChart } from 'lucide-react';

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
            setError("Invalid credentials. Please verify your email and password.");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-background flex flex-col items-center justify-center p-4">
            <motion.div 
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.5, ease: "easeOut" }}
                className="w-full max-w-sm"
            >
                <div className="flex flex-col items-center mb-8">
                    <div className="w-14 h-14 bg-white rounded-2xl shadow-sm border border-slate-100 flex items-center justify-center mb-4">
                        <PieChart className="w-8 h-8 text-primary-500" />
                    </div>
                    <h1 className="text-2xl font-bold text-slate-800 tracking-tight">MenuMind</h1>
                    <p className="text-slate-500 text-sm mt-1">Engineer your success today.</p>
                </div>

                <Card className="p-8 border-slate-200 shadow-xl" hover={false}>
                    <form onSubmit={handleSubmit} className="space-y-5">
                        <Input 
                            label="Email Address" 
                            type="email" 
                            placeholder="admin@restaurant.com" 
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            required
                        />
                        <Input 
                            label="Password" 
                            type="password" 
                            placeholder="••••••••" 
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            required
                        />
                        
                        {error && (
                            <p className="text-red-500 text-sm font-medium">{error}</p>
                        )}
                        
                        <Button type="submit" className="w-full py-2.5 mt-2" disabled={loading}>
                            {loading ? 'Authenticating...' : 'Sign In'}
                        </Button>
                    </form>
                </Card>
            </motion.div>
        </div>
    );
}
