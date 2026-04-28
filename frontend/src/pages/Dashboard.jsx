import { useEffect, useMemo, useState } from 'react';
import { motion } from 'framer-motion';
import { Bar, BarChart, Cell, Legend, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { AlertCircle, DollarSign, PackageOpen, Sparkles, TrendingUp } from 'lucide-react';

import api from '../services/api';
import { MenuMatrix } from '../components/MenuMatrix';
import { useActiveRestaurant } from '../hooks/useActiveRestaurant';
import { Card } from '../ui/Card';
import { EmptyState } from '../ui/EmptyState';
import { Skeleton } from '../ui/Skeleton';

const money = (value) => `Rs ${Number(value || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

export default function Dashboard() {
    const activeRestaurant = useActiveRestaurant();
    const [classifications, setClassifications] = useState([]);
    const [insights, setInsights] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchAnalytics = async () => {
            if (!activeRestaurant) {
                setLoading(false);
                setClassifications([]);
                setInsights([]);
                return;
            }

            setLoading(true);
            try {
                const query = `restaurant_name=${encodeURIComponent(activeRestaurant)}`;
                const [classificationResponse, insightsResponse] = await Promise.all([
                    api.get(`/analytics/classification?${query}`),
                    api.get(`/analytics/insights?${query}`),
                ]);
                setClassifications(classificationResponse.data);
                setInsights(insightsResponse.data);
                setError(null);
            } catch (err) {
                setError(err.response?.data?.detail || "Failed to load analytics. Check the backend connection and selected restaurant.");
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
    const totalRevenue = classifications.reduce((sum, item) => sum + item.total_revenue, 0);
    const totalVolume = classifications.reduce((sum, item) => sum + item.total_quantity, 0);

    const chartData = useMemo(() => {
        return classifications
            .map(item => ({
                name: item.item_name,
                revenue: Number(item.total_revenue.toFixed(2)),
                profit: Number((item.profit * item.total_quantity).toFixed(2)),
            }))
            .sort((a, b) => b.revenue - a.revenue)
            .slice(0, 6);
    }, [classifications]);

    const pieData = useMemo(() => {
        const counts = { Star: 0, Plowhorse: 0, Puzzle: 0, Dog: 0 };
        classifications.forEach(c => { if (counts[c.category] !== undefined) counts[c.category]++; });
        return [
            { name: 'Stars', value: counts.Star, color: '#0f9f7a' },
            { name: 'Plowhorses', value: counts.Plowhorse, color: '#d79d16' },
            { name: 'Puzzles', value: counts.Puzzle, color: '#3f78d8' },
            { name: 'Dogs', value: counts.Dog, color: '#dc4a4a' },
        ].filter(d => d.value > 0);
    }, [classifications]);

    return (
        <div className="space-y-7 pb-10">
            <section className="relative overflow-hidden rounded-lg border border-white/70 bg-ink-900 text-white shadow-soft">
                <div
                    className="absolute inset-0 opacity-30 bg-cover bg-center"
                    style={{ backgroundImage: "url('https://images.unsplash.com/photo-1552566626-52f8b828add9?auto=format&fit=crop&w=1600&q=80')" }}
                />
                <div className="absolute inset-0 bg-gradient-to-r from-ink-900 via-ink-900/85 to-primary-700/50" />
                <div className="relative p-6 sm:p-8 flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
                    <div>
                        <p className="text-xs font-bold uppercase tracking-[0.24em] text-primary-100">Menu intelligence cockpit</p>
                        <h1 className="text-3xl sm:text-4xl font-black tracking-tight mt-2">Executive Dashboard</h1>
                        <p className="text-sm text-white/75 max-w-2xl mt-3">
                            Analyze sales, margin, product mix, and menu-engineering categories from the selected restaurant.
                        </p>
                    </div>
                    <div className="rounded-md border border-white/15 bg-white/10 px-4 py-3">
                        <p className="text-xs uppercase tracking-widest text-white/60">Active restaurant</p>
                        <p className="font-bold text-lg truncate max-w-[280px]">{activeRestaurant || 'No data selected'}</p>
                    </div>
                </div>
            </section>

            {error ? (
                <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="p-5 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3 shadow-sm">
                    <AlertCircle className="w-5 h-5 text-red-500 mt-0.5 shrink-0" />
                    <div>
                        <h3 className="text-sm font-bold text-red-800">System Error</h3>
                        <p className="text-sm text-red-600 mt-1">{error}</p>
                    </div>
                </motion.div>
            ) : !activeRestaurant ? (
                <EmptyState title="No restaurant selected" message="Upload a sales file to create your first restaurant workspace." />
            ) : (
                <>
                    <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-5">
                        <MetricCard icon={DollarSign} label="Total Revenue" loading={loading} value={money(totalRevenue)} />
                        <MetricCard icon={TrendingUp} label="Estimated Gross Profit" loading={loading} value={money(totalProfit)} />
                        <MetricCard icon={PackageOpen} label="Units Sold" loading={loading} value={totalVolume.toLocaleString()} />
                        <MetricCard icon={Sparkles} label="Top Profit Driver" loading={loading} value={topPerformer?.item_name || 'No Data'} highlight />
                    </div>

                    {insights.length > 0 && (
                        <div className="grid grid-cols-1 lg:grid-cols-5 gap-4">
                            {insights.slice(0, 5).map((insight) => (
                                <Card key={insight.title} className="p-4">
                                    <p className="text-xs font-bold uppercase tracking-widest text-slate-400">{insight.title}</p>
                                    <p className="font-extrabold text-slate-900 mt-2 leading-tight">{insight.value}</p>
                                    <p className="text-xs text-slate-500 mt-2 leading-relaxed">{insight.detail}</p>
                                </Card>
                            ))}
                        </div>
                    )}

                    {!loading && classifications.length > 0 && (
                        <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
                            <Card className="lg:col-span-2 p-6 border-slate-200">
                                <h3 className="text-sm font-bold text-slate-800 uppercase tracking-widest mb-6">Top Revenue Drivers</h3>
                                <div className="h-[300px] w-full">
                                    <ResponsiveContainer width="100%" height="100%">
                                        <BarChart data={chartData} margin={{ top: 0, right: 0, left: -10, bottom: 0 }}>
                                            <XAxis dataKey="name" tick={{ fontSize: 12, fill: '#64748b' }} tickLine={false} axisLine={false} />
                                            <YAxis tick={{ fontSize: 12, fill: '#64748b' }} tickLine={false} axisLine={false} tickFormatter={(value) => `Rs ${value}`} />
                                            <Tooltip cursor={{ fill: '#f1f5f9' }} contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 18px 45px -30px rgba(0,0,0,0.35)' }} />
                                            <Bar dataKey="revenue" radius={[6, 6, 0, 0]}>
                                                {chartData.map((entry, index) => (
                                                    <Cell key={`cell-${index}`} fill={index === 0 ? '#0f9f7a' : '#8aa99e'} />
                                                ))}
                                            </Bar>
                                        </BarChart>
                                    </ResponsiveContainer>
                                </div>
                            </Card>

                            <Card className="p-6 border-slate-200 flex flex-col items-center">
                                <h3 className="text-sm font-bold text-slate-800 uppercase tracking-widest w-full text-left mb-2">Category Spread</h3>
                                <div className="h-[280px] w-full relative">
                                    <ResponsiveContainer width="100%" height="100%">
                                        <PieChart>
                                            <Pie data={pieData} cx="50%" cy="50%" innerRadius={62} outerRadius={88} paddingAngle={5} dataKey="value" stroke="none">
                                                {pieData.map((entry, index) => <Cell key={`cell-${index}`} fill={entry.color} />)}
                                            </Pie>
                                            <Tooltip contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 18px 45px -30px rgba(0,0,0,0.35)' }} />
                                            <Legend verticalAlign="bottom" height={36} iconType="circle" wrapperStyle={{ fontSize: '12px', fontWeight: '600' }} />
                                        </PieChart>
                                    </ResponsiveContainer>
                                    <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none mt-[-36px]">
                                        <span className="text-2xl font-extrabold text-slate-900">{classifications.length}</span>
                                        <span className="text-[10px] uppercase tracking-widest text-slate-500 font-bold">Items</span>
                                    </div>
                                </div>
                            </Card>
                        </div>
                    )}

                    <div className="pt-3">
                        <div className="mb-5">
                            <h2 className="text-lg font-bold text-slate-900">Menu Engineering Matrix</h2>
                            <p className="text-sm text-slate-500 mt-1">Items are classified by demand and estimated per-unit profitability.</p>
                        </div>

                        {loading ? (
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                                {[1, 2, 3, 4].map(i => (
                                    <Card key={i} animate={false} className="p-5 h-[360px] border-slate-100 flex flex-col gap-4 shadow-sm">
                                        <Skeleton className="h-6 w-24" />
                                        <Skeleton className="h-[68px] w-full rounded-md" />
                                        <Skeleton className="h-[68px] w-full rounded-md" />
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

function MetricCard({ icon: Icon, label, value, loading, highlight = false }) {
    return (
        <Card animate hover className={`p-5 relative overflow-hidden group ${highlight ? 'bg-ink-900 text-white' : ''}`}>
            <div className={`absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity ${highlight ? 'text-white' : 'text-primary-600'}`}>
                <Icon className="w-16 h-16" />
            </div>
            <p className={`text-xs font-bold mb-2 tracking-widest uppercase ${highlight ? 'text-white/60' : 'text-slate-500'}`}>{label}</p>
            {loading ? <Skeleton className="h-8 w-32 mt-1" /> : (
                <h2 className={`text-2xl font-black tracking-tight truncate ${highlight ? 'text-white' : 'text-slate-900'}`} title={value}>{value}</h2>
            )}
        </Card>
    );
}
