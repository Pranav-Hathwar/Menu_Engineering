import { useEffect, useState } from 'react';
import { Card } from '../ui/Card';
import { Badge } from '../ui/Badge';
import { Button } from '../ui/Button';
import { MenuMatrix } from '../components/MenuMatrix';
import { Skeleton } from '../ui/Skeleton';
import { EmptyState } from '../ui/EmptyState';
import api from '../services/api';
import { AlertCircle } from 'lucide-react';
import { motion } from 'framer-motion';

export default function Dashboard() {
    const [classifications, setClassifications] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchAnalytics = async () => {
            try {
                const response = await api.get('/analytics/classification');
                setClassifications(response.data);
                setError(null);
            } catch (err) {
                // Return exact operational failures gracefully
                setError(err.response?.data?.detail || "Failed to load analytical data. Please verify your connection.");
            } finally {
                setLoading(false);
            }
        };
        fetchAnalytics();
    }, []);

    // Dynamically derive dashboard metrics from arrays to maintain visual integrity
    const topPerformer = classifications.length > 0 
        ? classifications.reduce((prev, current) => (prev.profit * prev.total_quantity > current.profit * current.total_quantity) ? prev : current)
        : null;

    const totalProfit = classifications.reduce((sum, item) => sum + (item.profit * item.total_quantity), 0);

    return (
        <div className="space-y-8">
            <div>
                <h1 className="text-2xl font-bold text-slate-800 tracking-tight">Menu Insights Overview</h1>
                <p className="text-slate-500 text-sm mt-1">Your high-level performance snapshot and categorization matrix.</p>
            </div>

            {error ? (
                <motion.div initial={{opacity:0}} animate={{opacity:1}} className="p-5 bg-red-50 border border-red-200 rounded-xl flex items-start gap-3 shadow-sm">
                    <AlertCircle className="w-5 h-5 text-red-500 mt-0.5 shrink-0" />
                    <div>
                        <h3 className="text-sm font-bold text-red-800">System Error</h3>
                        <p className="text-sm text-red-600 mt-1">{error}</p>
                        <Button variant="danger" className="mt-4 text-xs py-1.5 font-bold tracking-wide uppercase" onClick={() => window.location.reload()}>Retry Connection</Button>
                    </div>
                </motion.div>
            ) : (
                <>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                        <Card animate hover className="p-6">
                            <p className="text-sm font-medium text-slate-500 mb-1">Total Matrix Profit</p>
                            {loading ? <Skeleton className="h-9 w-32 mt-1" /> : (
                                <>
                                <h2 className="text-3xl font-extrabold text-slate-800">${totalProfit.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}</h2>
                                <p className="text-xs text-primary-600 font-semibold mt-2 flex items-center gap-1">
                                    Computed from structural matrix
                                </p>
                                </>
                            )}
                        </Card>
                        <Card animate hover className="p-6">
                            <p className="text-sm font-medium text-slate-500 mb-1">Active Menu Items</p>
                            {loading ? <Skeleton className="h-9 w-16 mt-1" /> : (
                                <>
                                <h2 className="text-3xl font-extrabold text-slate-800">{classifications.length}</h2>
                                <p className="text-xs text-slate-500 font-medium mt-2">
                                    Identified categorized profiles
                                </p>
                                </>
                            )}
                        </Card>
                        <Card animate hover className="p-6 bg-gradient-to-br from-primary-500 to-primary-600 border-transparent text-white shadow-md">
                            <p className="text-sm font-medium text-primary-100 mb-1">Top Performer Engine</p>
                            {loading ? (
                                <div className="mt-1 space-y-3">
                                    <Skeleton className="h-8 w-48 bg-white/20" />
                                    <Skeleton className="h-5 w-20 rounded-full bg-white/20" />
                                </div>
                            ) : (
                                <>
                                <h2 className="text-2xl font-bold text-white tracking-tight truncate" title={topPerformer?.item_name || 'Awaiting Data'}>
                                    {topPerformer ? topPerformer.item_name : 'Awaiting Data'}
                                </h2>
                                <div className="mt-3">
                                    <Badge type="default" className="bg-white/20 text-white font-semibold border-transparent shadow-[inset_0_1px_0_rgba(255,255,255,0.2)]">
                                        {topPerformer ? topPerformer.category : 'Standby'}
                                    </Badge>
                                </div>
                                </>
                            )}
                        </Card>
                    </div>

                    <div>
                        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-4 mt-8">
                            <h2 className="text-lg font-bold text-slate-800">Menu Engineering Matrix</h2>
                            <Button variant="secondary" className="text-sm py-1.5 px-4 font-semibold w-full sm:w-auto" disabled={loading || classifications.length === 0}>
                                Export Strategies
                            </Button>
                        </div>
                        
                        {loading ? (
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 w-full max-w-full">
                                {[1,2,3,4].map(i => (
                                    <Card key={i} animate={false} className="p-5 h-[420px] border-slate-100 flex flex-col gap-4 shadow-sm">
                                        <div className="space-y-2 mb-2">
                                            <Skeleton className="h-6 w-24" />
                                            <Skeleton className="h-3 w-48" />
                                        </div>
                                        <div className="space-y-3 flex-1">
                                            <Skeleton className="h-[68px] w-full rounded-xl" />
                                            <Skeleton className="h-[68px] w-full rounded-xl" />
                                            <Skeleton className="h-[68px] w-full rounded-xl" />
                                        </div>
                                    </Card>
                                ))}
                            </div>
                        ) : classifications.length === 0 ? (
                            <EmptyState />
                        ) : (
                            <MenuMatrix classifications={classifications} />
                        )}
                    </div>
                </>
            )}
        </div>
    );
}
