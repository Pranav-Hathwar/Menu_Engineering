import { useEffect, useState } from 'react';
import { Card } from '../ui/Card';
import { Skeleton } from '../ui/Skeleton';
import { EmptyState } from '../ui/EmptyState';
import api from '../services/api';
import { useActiveRestaurant } from '../hooks/useActiveRestaurant';
import { Database, AlertCircle } from 'lucide-react';

export default function RawData() {
    const activeRestaurant = useActiveRestaurant();
    const [rows, setRows] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchRawData = async () => {
            if (!activeRestaurant) return;
            setLoading(true);
            try {
                const response = await api.get(`/analytics/raw?restaurant_name=${encodeURIComponent(activeRestaurant)}`);
                setRows(response.data);
                setError(null);
            } catch (err) {
                setError(err.response?.data?.detail || "Failed to load raw file data.");
            } finally {
                setLoading(false);
            }
        };
        fetchRawData();
    }, [activeRestaurant]);

    return (
        <div className="space-y-8">
            <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-white rounded-xl shadow-sm border border-slate-200 flex items-center justify-center">
                    <Database className="w-6 h-6 text-primary-600" />
                </div>
                <div>
                    <h1 className="text-2xl font-bold text-slate-800 tracking-tight">Raw Uploaded Data</h1>
                    <p className="text-slate-500 text-sm mt-1">A direct mirror of your uploaded spreadsheets securely parsed in the database.</p>
                </div>
            </div>

            {error ? (
                <div className="p-5 bg-red-50 border border-red-200 rounded-xl flex items-start gap-3 shadow-sm">
                    <AlertCircle className="w-5 h-5 text-red-500 mt-0.5 shrink-0" />
                    <div>
                        <h3 className="text-sm font-bold text-red-800">Data Load Failure</h3>
                        <p className="text-sm text-red-600 mt-1">{error}</p>
                    </div>
                </div>
            ) : loading ? (
                <Card className="p-6 space-y-4">
                    {[1,2,3,4,5,6].map(i => <Skeleton key={i} className="h-10 w-full" />)}
                </Card>
            ) : rows.length === 0 ? (
                <EmptyState message="No raw sales data found for this tenant. Upload a file first." />
            ) : (
                <Card className="overflow-hidden border-slate-200 shadow-sm">
                    <div className="overflow-x-auto">
                        <table className="w-full text-sm text-left align-middle text-slate-800">
                            <thead className="text-xs text-slate-500 uppercase bg-slate-50 border-b border-slate-100 font-semibold tracking-wider">
                                <tr>
                                    <th scope="col" className="px-6 py-4">Database ID</th>
                                    <th scope="col" className="px-6 py-4">Log Date</th>
                                    <th scope="col" className="px-6 py-4">Parsed Item Name</th>
                                    <th scope="col" className="px-6 py-4 text-right">Quantity</th>
                                    <th scope="col" className="px-6 py-4 text-right">Raw Revenue</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-100/60">
                                {rows.map((row) => (
                                    <tr key={row.id} className="hover:bg-slate-50/50 transition-colors">
                                        <td className="px-6 py-4 text-xs font-mono text-slate-400">
                                            #{row.id}
                                        </td>
                                        <td className="px-6 py-4 text-slate-600">
                                            {row.date}
                                        </td>
                                        <td className="px-6 py-4 font-bold text-slate-700">
                                            {row.item_name}
                                        </td>
                                        <td className="px-6 py-4 text-right font-semibold text-slate-600">
                                            {row.quantity.toLocaleString()}
                                        </td>
                                        <td className="px-6 py-4 text-right font-mono font-medium text-slate-600">
                                            ₹{parseFloat(row.revenue).toFixed(2)}
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
