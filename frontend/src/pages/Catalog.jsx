import { useEffect, useState } from 'react';
import { Card } from '../ui/Card';
import { Skeleton } from '../ui/Skeleton';
import { EmptyState } from '../ui/EmptyState';
import api from '../services/api';
import { useActiveRestaurant } from '../hooks/useActiveRestaurant';
import { AlertCircle, ListFilter } from 'lucide-react';

export default function Catalog() {
    const activeRestaurant = useActiveRestaurant();
    const [items, setItems] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    // Advanced Data Filtering Parameters
    const [searchTerm, setSearchTerm] = useState('');
    const [filterCategory, setFilterCategory] = useState('All');

    useEffect(() => {
        const fetchCatalog = async () => {
            if (!activeRestaurant) return;
            setLoading(true);
            try {
                const response = await api.get(`/analytics/classification?restaurant_name=${encodeURIComponent(activeRestaurant)}`);
                const sorted = response.data.sort((a, b) => b.total_quantity - a.total_quantity);
                setItems(sorted);
                setError(null);
            } catch (err) {
                setError(err.response?.data?.detail || "Failed to load Catalog data.");
            } finally {
                setLoading(false);
            }
        };
        fetchCatalog();
    }, [activeRestaurant]);

    const getMatrixColor = (category) => {
        switch(category) {
            case 'Star': return 'text-emerald-700 bg-emerald-50 ring-emerald-600/20';
            case 'Plowhorse': return 'text-yellow-700 bg-yellow-50 ring-yellow-600/20';
            case 'Puzzle': return 'text-blue-700 bg-blue-50 ring-blue-600/20';
            case 'Dog': return 'text-red-700 bg-red-50 ring-red-600/20';
            default: return 'text-slate-700 bg-slate-50 ring-slate-600/20';
        }
    }

    const getCategoryAdvice = (category) => {
        switch(category) {
            case 'Star': return {
                title: '🌟 Star Management Strategy',
                desc: 'These items drive your revenue. Maintain strict quality control, feature them prominently on your physical menu, and do not alter the recipe.',
                color: 'text-emerald-800 bg-emerald-50 border-emerald-200'
            };
            case 'Plowhorse': return {
                title: '🐎 Plowhorse Management Strategy',
                desc: 'These are your traffic drivers but their margins are too slim. Carefully increase prices slightly, reduce portion sizes invisibly, or lower ingredient costs to improve margins without dropping volume.',
                color: 'text-yellow-800 bg-yellow-50 border-yellow-200'
            };
            case 'Puzzle': return {
                title: '🧩 Puzzle Management Strategy',
                desc: 'These have fantastic margins but no one buys them. Reposition them to high-visibility spots on the menu (top right), rename them to sound more appealing, or have waitstaff run daily promotions.',
                color: 'text-blue-800 bg-blue-50 border-blue-200'
            };
            case 'Dog': return {
                title: '🐕 Dog Management Strategy',
                desc: 'These items are actively draining your kitchen resources with zero payoff. Strongly consider removing them from the menu entirely, or completely overhauling their recipe and price tier.',
                color: 'text-red-800 bg-red-50 border-red-200'
            };
            default: return null;
        }
    }

    return (
        <div className="space-y-8">
            <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-white rounded-xl shadow-sm border border-slate-200 flex items-center justify-center">
                    <ListFilter className="w-6 h-6 text-primary-600" />
                </div>
                <div>
                    <h1 className="text-2xl font-bold text-slate-800 tracking-tight">Global Item Catalog</h1>
                    <p className="text-slate-500 text-sm mt-1">Direct tabular view of all extracted item streams and computational groupings.</p>
                </div>
            </div>

            {/* Matrix Data Isolator Toolbar */}
            <div className="flex flex-col sm:flex-row items-center justify-between gap-4 p-4 bg-white border border-slate-200 rounded-xl shadow-sm">
                <input 
                    type="text" 
                    placeholder="Search explicitly by Item Name..."
                    value={searchTerm}
                    onChange={e => setSearchTerm(e.target.value)}
                    className="w-full sm:max-w-sm px-4 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm text-slate-800 focus:outline-none focus:ring-2 focus:ring-primary-500/30 focus:border-primary-500 transition-colors"
                />
                <select 
                    value={filterCategory}
                    onChange={e => setFilterCategory(e.target.value)}
                    className="w-full sm:max-w-[200px] px-4 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm text-slate-700 font-semibold focus:outline-none focus:ring-2 focus:ring-primary-500/30 transition-colors cursor-pointer"
                >
                    <option value="All">All Categories</option>
                    <option value="Star">Stars</option>
                    <option value="Plowhorse">Plowhorses</option>
                    <option value="Puzzle">Puzzles</option>
                    <option value="Dog">Dogs</option>
                </select>
            </div>

            {/* Strategic Advice Banner (Shows dynamically when filtered) */}
            {filterCategory !== 'All' && getCategoryAdvice(filterCategory) && (
                <div className={`p-5 -mt-4 border rounded-xl shadow-[0_2px_10px_-4px_rgba(0,0,0,0.1)] flex flex-col gap-1 transition-all ${getCategoryAdvice(filterCategory).color}`}>
                    <h3 className="text-sm font-extrabold tracking-tight">{getCategoryAdvice(filterCategory).title}</h3>
                    <p className="text-sm font-medium opacity-90 leading-relaxed max-w-4xl">{getCategoryAdvice(filterCategory).desc}</p>
                </div>
            )}

            {error ? (
                <div className="p-5 bg-red-50 border border-red-200 rounded-xl flex items-start gap-3 shadow-sm">
                    <AlertCircle className="w-5 h-5 text-red-500 mt-0.5 shrink-0" />
                    <div>
                        <h3 className="text-sm font-bold text-red-800">Catalog Load Failure</h3>
                        <p className="text-sm text-red-600 mt-1">{error}</p>
                    </div>
                </div>
            ) : loading ? (
                <Card className="p-0 overflow-hidden">
                    <div className="p-6 border-b border-slate-100 flex items-center gap-4">
                        <Skeleton className="h-6 w-32" />
                        <Skeleton className="h-6 w-48" />
                    </div>
                    <div className="p-6 space-y-4">
                        {[1,2,3,4,5].map(i => <Skeleton key={i} className="h-12 w-full" />)}
                    </div>
                </Card>
            ) : items.length === 0 ? (
                <EmptyState message="Your item catalog is effectively empty. Upload data first." />
            ) : (
                <Card className="overflow-hidden border-slate-200 shadow-sm">
                    <div className="overflow-x-auto">
                        <table className="w-full text-sm text-left align-middle text-slate-800">
                            <thead className="text-xs text-slate-500 uppercase bg-slate-50 border-b border-slate-100 font-semibold tracking-wider">
                                <tr>
                                    <th scope="col" className="px-6 py-4">Menu Item</th>
                                    <th scope="col" className="px-6 py-4 text-center">Category Group</th>
                                    <th scope="col" className="px-6 py-4 text-right">Units Sold</th>
                                    <th scope="col" className="px-6 py-4 text-right">Unit COGS</th>
                                    <th scope="col" className="px-6 py-4 text-right">Total Revenue</th>
                                    <th scope="col" className="px-6 py-4 text-right">Total Profit</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-100/60">
                                {items
                                    .filter(item => {
                                        const matchesSearch = item.item_name.toLowerCase().includes(searchTerm.toLowerCase());
                                        const matchesCat = filterCategory === 'All' ? true : item.category === filterCategory;
                                        return matchesSearch && matchesCat;
                                    })
                                    .map((item, index) => (
                                    <tr key={index} className="hover:bg-slate-50/50 transition-colors">
                                        <td className="px-6 py-4 font-bold text-slate-700">
                                            {item.item_name}
                                        </td>
                                        <td className="px-6 py-4 text-center">
                                            <span className={`inline-flex items-center px-2 py-1 rounded-md text-xs font-bold ring-1 ring-inset ${getMatrixColor(item.category)}`}>
                                                {item.category}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4 text-right font-semibold text-slate-600">
                                            {item.total_quantity.toLocaleString()}
                                        </td>
                                        <td className="px-6 py-4 text-right font-mono font-medium text-red-600">
                                            ₹{parseFloat(item.unit_cost).toFixed(2)}
                                        </td>
                                        <td className="px-6 py-4 text-right font-mono font-medium text-slate-600">
                                            ₹{parseFloat(item.total_revenue).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}
                                        </td>
                                        <td className="px-6 py-4 text-right font-mono font-bold text-emerald-700 bg-emerald-50/20">
                                            ₹{parseFloat(item.profit * item.total_quantity).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </Card>
            )}
        </div>
    );
}
