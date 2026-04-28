import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { AlertCircle, BrainCircuit, LineChart, Sparkles, Target, TrendingDown, TrendingUp } from 'lucide-react';

import api from '../services/api';
import { useActiveRestaurant } from '../hooks/useActiveRestaurant';
import { Badge } from '../ui/Badge';
import { Card } from '../ui/Card';
import { EmptyState } from '../ui/EmptyState';
import { Skeleton } from '../ui/Skeleton';

export default function Insights() {
    const activeRestaurant = useActiveRestaurant();
    const [recommendations, setRecommendations] = useState([]);
    const [insights, setInsights] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchInsights = async () => {
            if (!activeRestaurant) {
                setLoading(false);
                return;
            }
            setLoading(true);
            try {
                const query = `restaurant_name=${encodeURIComponent(activeRestaurant)}`;
                const [recommendationResponse, insightResponse] = await Promise.all([
                    api.get(`/analytics/recommendations?${query}`),
                    api.get(`/analytics/insights?${query}`),
                ]);
                setRecommendations(recommendationResponse.data);
                setInsights(insightResponse.data);
                setError(null);
            } catch (err) {
                setError(err.response?.data?.detail || "Failed to load recommendations.");
            } finally {
                setLoading(false);
            }
        };
        fetchInsights();
    }, [activeRestaurant]);

    const getPriorityColor = (priority) => {
        switch (priority) {
            case 'High': return 'bg-red-50 text-red-700 border-red-200';
            case 'Medium': return 'bg-yellow-50 text-yellow-700 border-yellow-200';
            case 'Low': return 'bg-emerald-50 text-emerald-700 border-emerald-200';
            default: return 'bg-slate-50 text-slate-700 border-slate-200';
        }
    };

    const getCategoryIcon = (category) => {
        switch (category) {
            case 'Star': return <Sparkles className="w-5 h-5 text-emerald-500" />;
            case 'Plowhorse': return <TrendingUp className="w-5 h-5 text-yellow-500" />;
            case 'Puzzle': return <Target className="w-5 h-5 text-blue-500" />;
            case 'Dog': return <TrendingDown className="w-5 h-5 text-red-500" />;
            default: return <BrainCircuit className="w-5 h-5 text-slate-500" />;
        }
    };

    return (
        <div className="space-y-7">
            <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-ink-900 rounded-lg shadow-sm flex items-center justify-center">
                    <BrainCircuit className="w-6 h-6 text-primary-100" />
                </div>
                <div>
                    <p className="text-xs font-bold uppercase tracking-[0.24em] text-primary-700">Decision layer</p>
                    <h1 className="text-3xl font-black text-slate-900 tracking-tight mt-1">Insights & Strategies</h1>
                    <p className="text-slate-500 text-sm mt-1">Rule-based recommendations and operational signals from your sales data.</p>
                </div>
            </div>

            {error ? (
                <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="p-5 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3 shadow-sm">
                    <AlertCircle className="w-5 h-5 text-red-500 mt-0.5 shrink-0" />
                    <div>
                        <h3 className="text-sm font-bold text-red-800">Insights Load Error</h3>
                        <p className="text-sm text-red-600 mt-1">{error}</p>
                    </div>
                </motion.div>
            ) : loading ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
                    {[1, 2, 3, 4, 5, 6].map(i => (
                        <Card key={i} animate={false} className="p-6 h-[220px] flex flex-col justify-between">
                            <div className="space-y-3">
                                <Skeleton className="h-6 w-1/2" />
                                <Skeleton className="h-4 w-full" />
                                <Skeleton className="h-4 w-5/6" />
                            </div>
                            <Skeleton className="h-8 w-24 rounded-md" />
                        </Card>
                    ))}
                </div>
            ) : recommendations.length === 0 ? (
                <EmptyState message="No recommendations available. Upload sales data to initialize the analytics engine." />
            ) : (
                <>
                    {insights.length > 0 && (
                        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-5 gap-4">
                            {insights.map((insight) => (
                                <Card key={insight.title} className="p-4">
                                    <LineChart className="w-4 h-4 text-primary-600 mb-3" />
                                    <p className="text-xs font-bold uppercase tracking-widest text-slate-400">{insight.title}</p>
                                    <p className="font-black text-slate-900 mt-2 leading-tight">{insight.value}</p>
                                    <p className="text-xs text-slate-500 mt-2 leading-relaxed">{insight.detail}</p>
                                </Card>
                            ))}
                        </div>
                    )}

                    <div className="grid grid-cols-1 xl:grid-cols-3 md:grid-cols-2 gap-5">
                        {recommendations.map((rec, index) => (
                            <Card key={`${rec.item_name}-${index}`} animate hover className="p-6 border-slate-100 flex flex-col justify-between h-full bg-white shadow-sm hover:shadow-md transition-all">
                                <div>
                                    <div className="flex justify-between items-start gap-3 mb-4">
                                        <div className="flex items-center gap-2 min-w-0">
                                            {getCategoryIcon(rec.category)}
                                            <h3 className="font-black text-slate-900 text-lg truncate" title={rec.item_name}>
                                                {rec.item_name}
                                            </h3>
                                        </div>
                                        <span className={`text-[10px] font-bold uppercase tracking-wider px-2.5 py-1 rounded-md border shrink-0 ${getPriorityColor(rec.priority)}`}>
                                            {rec.priority}
                                        </span>
                                    </div>

                                    <div className="bg-slate-50 p-4 rounded-md border border-slate-100 mb-4">
                                        <p className="text-sm font-semibold text-slate-900 leading-snug">{rec.recommendation}</p>
                                    </div>
                                    <p className="text-xs text-slate-500 font-medium mb-4">
                                        <span className="font-bold text-slate-700">Why:</span> {rec.reason}
                                    </p>
                                </div>

                                <div className="mt-auto border-t border-slate-100 pt-4 flex justify-between items-center">
                                    <span className="text-[11px] font-bold text-slate-400 tracking-wider uppercase">Classified As</span>
                                    <Badge type="default" className="bg-slate-100 text-slate-700 border-slate-200">
                                        {rec.category}
                                    </Badge>
                                </div>
                            </Card>
                        ))}
                    </div>
                </>
            )}
        </div>
    );
}
