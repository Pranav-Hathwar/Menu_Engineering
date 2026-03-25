import { useEffect, useState, useMemo } from 'react';
import { Card } from '../ui/Card';
import { Badge } from '../ui/Badge';
import { MenuMatrix } from '../components/MenuMatrix';
import { Skeleton } from '../ui/Skeleton';
import { EmptyState } from '../ui/EmptyState';
import api from '../services/api';
import { useActiveRestaurant } from '../hooks/useActiveRestaurant';
import { AlertCircle, TrendingUp, DollarSign, PackageOpen } from 'lucide-react';
import { motion } from 'framer-motion';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, PieChart, Pie, Legend } from 'recharts';

export default function Dashboard() {
    const activeRestaurant = useActiveRestaurant();
    const [classifications, setClassifications] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchAnalytics = async () => {
            if (!activeRestaurant) return;
            setLoading(true);
            try {
                const response = await api.get(`/analytics/classification?restaurant_name=${encodeURIComponent(activeRestaurant)}`);
                setClassifications(response.data);
                setError(null);
            } catch (err) {
                setError(err.response?.data?.detail || "Failed to load analytical data. Please verify your connection.");
            } finally {
                setLoading(false);
            }
        };
        fetchAnalytics();
    }, [activeRestaurant]);

    const topPerformer = useMemo(() => {
        if (!classifications.length) return null;
        return classifications.reduce((prev, current) => 
            (prev.profit * prev.total_quantity > current.profit * current.total_quantity) ? prev : current
        );
    }, [classifications]);

    const totalProfit = classifications.reduce((sum, item) => sum + (item.profit * item.total_quantity), 0);
    const totalVolume = classifications.reduce((sum, item) => sum + item.total_quantity, 0);

    // Prepare robust Chart Data cleanly
    const chartData = useMemo(() => {
        return classifications
            .map(item => ({
                name: item.item_name,
                revenue: Number((item.profit * item.total_quantity).toFixed(2)),
                volume: item.total_quantity
            }))
            .sort((a, b) => b.revenue - a.revenue)
            .slice(0, 6); // Top 6 items by revenue
    }, [classifications]);

    const pieData = useMemo(() => {
        const counts = { Star: 0, Plowhorse: 0, Puzzle: 0, Dog: 0 };
        classifications.forEach(c => { if (counts[c.category] !== undefined) counts[c.category]++; });
        return [
            { name: 'Stars', value: counts.Star, color: '#10b981' },     // Emerald
            { name: 'Plowhorses', value: counts.Plowhorse, color: '#eab308' }, // Yellow
            { name: 'Puzzles', value: counts.Puzzle, color: '#3b82f6' },     // Blue
            { name: 'Dogs', value: counts.Dog, color: '#ef4444' },         // Red
        ].filter(d => d.value > 0);
    }, [classifications]);

    return (
        <div className="space-y-8 pb-10">
            <div>
                <h1 className="text-2xl font-bold text-slate-800 tracking-tight">Executive Dashboard</h1>
                <p className="text-slate-500 text-sm mt-1">Real-time analytical graphs, catalog summaries, and the BCG categorization matrix.</p>
            </div>

            {error ? (
                <motion.div initial={{opacity:0}} animate={{opacity:1}} className="p-5 bg-red-50 border border-red-200 rounded-xl flex items-start gap-3 shadow-sm">
                    <AlertCircle className="w-5 h-5 text-red-500 mt-0.5 shrink-0" />
                    <div>
                        <h3 className="text-sm font-bold text-red-800">System Error</h3>
                        <p className="text-sm text-red-600 mt-1">{error}</p>
                    </div>
                </motion.div>
            ) : (
                <>
                    {/* TOP KPI CARDS */}
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                        <Card animate hover className="p-6 relative overflow-hidden group">
                            <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
                                <DollarSign className="w-16 h-16 text-primary-500" />
                            </div>
                            <p className="text-sm font-semibold text-slate-500 mb-1 tracking-wide uppercase">Gross Matrix Revenue</p>
                            {loading ? <Skeleton className="h-9 w-32 mt-1" /> : (
                                <h2 className="text-3xl font-extrabold text-slate-800">₹{totalProfit.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}</h2>
                            )}
                        </Card>
                        
                        <Card animate hover className="p-6 relative overflow-hidden group">
                            <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
                                <PackageOpen className="w-16 h-16 text-emerald-500" />
                            </div>
                            <p className="text-sm font-semibold text-slate-500 mb-1 tracking-wide uppercase">Total Units Sold</p>
                            {loading ? <Skeleton className="h-9 w-24 mt-1" /> : (
                                <h2 className="text-3xl font-extrabold text-slate-800">{totalVolume.toLocaleString()}</h2>
                            )}
                        </Card>

                        <Card animate hover className="p-6 relative overflow-hidden group">
                            <p className="text-sm font-semibold text-slate-500 mb-1 tracking-wide uppercase">Active Catalog Scope</p>
                            {loading ? <Skeleton className="h-9 w-16 mt-1" /> : (
                                <h2 className="text-3xl font-extrabold text-slate-800">{classifications.length} <span className="text-lg font-medium text-slate-400">items</span></h2>
                            )}
                        </Card>

                        <Card animate hover className="p-6 bg-gradient-to-br from-primary-500 to-primary-600 border-transparent text-white shadow-md relative overflow-hidden group">
                            <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
                                <TrendingUp className="w-16 h-16 text-white" />
                            </div>
                            <p className="text-sm font-medium text-primary-100 mb-1 tracking-wide uppercase">Engine Winner</p>
                            {loading ? (
                                <div className="mt-1 space-y-3">
                                    <Skeleton className="h-8 w-48 bg-white/20" />
                                </div>
                            ) : (
                                <>
                                <h2 className="text-3xl font-extrabold text-white tracking-tight truncate pb-1" title={topPerformer?.item_name || 'Awaiting Data'}>
                                    {topPerformer ? topPerformer.item_name : 'No Data'}
                                </h2>
                                </>
                            )}
                        </Card>
                    </div>

                    {/* GRAPHS ROW */}
                    {(!loading && classifications.length > 0) && (
                        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mt-8">
                            <Card className="lg:col-span-2 p-6 border-slate-200">
                                <h3 className="text-sm font-bold text-slate-800 uppercase tracking-widest mb-6">Top 6 Drivers (By Revenue)</h3>
                                <div className="h-[280px] w-full">
                                    <ResponsiveContainer width="100%" height="100%">
                                        <BarChart data={chartData} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
                                            <XAxis dataKey="name" tick={{fontSize: 12, fill: '#64748b'}} tickLine={false} axisLine={false} />
                                            <YAxis tick={{fontSize: 12, fill: '#64748b'}} tickLine={false} axisLine={false} tickFormatter={(value) => `₹${value}`} />
                                            <Tooltip 
                                                cursor={{fill: '#f1f5f9'}} 
                                                contentStyle={{borderRadius: '12px', border: 'none', boxShadow: '0 4px 20px -2px rgba(0,0,0,0.1)'}}
                                            />
                                            <Bar dataKey="revenue" radius={[6, 6, 6, 6]}>
                                                {chartData.map((entry, index) => (
                                                    <Cell key={`cell-${index}`} fill={index === 0 ? '#10b981' : '#94a3b8'} />
                                                ))}
                                            </Bar>
                                        </BarChart>
                                    </ResponsiveContainer>
                                </div>
                            </Card>

                            <Card className="p-6 border-slate-200 flex flex-col items-center">
                                <h3 className="text-sm font-bold text-slate-800 uppercase tracking-widest w-full text-left mb-2">Category Spread</h3>
                                <div className="h-[260px] w-full relative">
                                    <ResponsiveContainer width="100%" height="100%">
                                        <PieChart>
                                            <Pie
                                                data={pieData}
                                                cx="50%"
                                                cy="50%"
                                                innerRadius={60}
                                                outerRadius={85}
                                                paddingAngle={5}
                                                dataKey="value"
                                                stroke="none"
                                            >
                                                {pieData.map((entry, index) => (
                                                    <Cell key={`cell-${index}`} fill={entry.color} />
                                                ))}
                                            </Pie>
                                            <Tooltip 
                                                contentStyle={{borderRadius: '12px', border: 'none', boxShadow: '0 4px 20px -2px rgba(0,0,0,0.1)'}}
                                                itemStyle={{fontWeight: 'bold', color: '#1e293b'}}
                                            />
                                            <Legend verticalAlign="bottom" height={36} iconType="circle" wrapperStyle={{fontSize: '12px', fontWeight: '600'}}/>
                                        </PieChart>
                                    </ResponsiveContainer>
                                    {/* Center KPI in Pie */}
                                    <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none mt-[-36px]">
                                        <span className="text-2xl font-extrabold text-slate-800">{classifications.length}</span>
                                        <span className="text-[10px] uppercase tracking-widest text-slate-500 font-bold">Items</span>
                                    </div>
                                </div>
                            </Card>
                        </div>
                    )}

                    {/* THE MATRIX */}
                    <div className="mt-8 pt-6 border-t border-slate-100">
                        <div className="mb-6">
                            <h2 className="text-lg font-bold text-slate-800">Menu Engineering Matrix</h2>
                            <p className="text-sm text-slate-500 mb-1">Drag constraints visually represent AI deterministic grouping architectures.</p>
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
