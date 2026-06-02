import { useState } from 'react';
import { motion } from 'framer-motion';
import { AlertCircle, CheckCircle2, File, UploadCloud } from 'lucide-react';

import api from '../services/api';
import { Button } from '../ui/Button';
import { Card } from '../ui/Card';
import { getErrorMessage, integer, money } from '../utils/format';

export default function Upload() {
    const [file, setFile] = useState(null);
    const [restaurantName, setRestaurantName] = useState('');
    const [loading, setLoading] = useState(false);
    const [status, setStatus] = useState(null);
    const [message, setMessage] = useState('');
    const [result, setResult] = useState(null);

    const handleFileChange = (e) => {
        if (e.target.files && e.target.files[0]) {
            setFile(e.target.files[0]);
            setStatus(null);
            setMessage('');
            setResult(null);
        }
    };

    const handleUpload = async () => {
        if (!file || !restaurantName.trim()) return;
        setLoading(true);
        setStatus(null);

        const formData = new FormData();
        formData.append('file', file);
        formData.append('restaurant_name', restaurantName.trim());

        try {
            const response = await api.post('/upload', formData);
            setStatus('success');
            setResult(response.data);
            setMessage(response.data.message || 'File processed successfully.');
            setFile(null);
            setRestaurantName('');
            window.dispatchEvent(new Event('restaurantUploaded'));
        } catch (error) {
            setStatus('error');
            setResult(null);
            setMessage(getErrorMessage(error, 'Failed to process file. Upload CSV, Excel, or JSON with item, quantity, revenue, and optional cost/date fields.'));
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="space-y-7">
            <div>
                <p className="text-xs font-bold uppercase tracking-[0.24em] text-primary-700">Ingestion pipeline</p>
                <h1 className="text-3xl font-black text-slate-900 tracking-tight mt-2">Data Input Hub</h1>
                <p className="text-slate-500 text-sm mt-2 max-w-2xl">
                    Upload CSV, Excel, or JSON sales exports. The parser detects headers, cleans values, normalizes rows, and rejects unusable records.
                </p>
            </div>

            <div className="grid grid-cols-1 xl:grid-cols-[1.15fr_0.85fr] gap-6">
                <Card className="p-6 sm:p-8 border-slate-200">
                    <div className="mb-6">
                        <label className="block text-sm font-bold text-slate-700 mb-2">Restaurant / Hotel Name <span className="text-red-500">*</span></label>
                        <input
                            type="text"
                            placeholder="e.g. Mint Masala"
                            value={restaurantName}
                            onChange={(e) => setRestaurantName(e.target.value)}
                            className="w-full px-4 py-3 rounded-md border border-slate-200 focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500 text-slate-900 transition-shadow bg-white"
                            required
                        />
                    </div>

                    <div className="border border-dashed border-primary-500/40 rounded-lg p-10 flex flex-col items-center justify-center bg-primary-50/40 text-center hover:bg-primary-50 transition-colors relative surface-grid">
                        <input
                            type="file"
                            accept=".csv,.json,.xlsx,.xls,application/json,text/csv,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,application/vnd.ms-excel"
                            onChange={handleFileChange}
                            className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                            aria-label="Upload sales file"
                        />

                        <div className="w-16 h-16 bg-white rounded-md flex items-center justify-center shadow-sm mb-4 border border-primary-100">
                            <UploadCloud className="w-8 h-8 text-primary-600" />
                        </div>
                        <h3 className="text-lg font-extrabold text-slate-900">Drop a sales export or select a file</h3>
                        <p className="text-sm text-slate-600 mt-2 max-w-md">
                            Supports messy CSVs, multi-sheet Excel files, and JSON records. Maximum size is 10 MB.
                        </p>
                    </div>

                    {file && (
                        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="mt-6 p-4 bg-white border border-slate-200 rounded-lg flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 shadow-sm">
                            <div className="flex items-center gap-3 min-w-0">
                                <File className="w-5 h-5 text-primary-700 shrink-0" />
                                <div className="min-w-0">
                                    <span className="text-sm font-bold text-slate-800 truncate block">{file.name}</span>
                                    <span className="text-xs text-slate-500">{(file.size / 1024).toFixed(1)} KB</span>
                                </div>
                            </div>
                            <Button onClick={handleUpload} disabled={loading || !restaurantName.trim()} className="px-6 shrink-0 font-semibold">
                                {loading ? 'Normalizing data...' : 'Process Upload'}
                            </Button>
                        </motion.div>
                    )}

                    {status === 'success' && (
                        <StatusPanel type="success" title="Ingestion Complete" message={message} result={result} />
                    )}

                    {status === 'error' && (
                        <StatusPanel type="error" title="Ingestion Failed" message={message} />
                    )}
                </Card>

                <Card className="overflow-hidden border-slate-200">
                    <div
                        className="h-48 bg-cover bg-center"
                        style={{ backgroundImage: "url('https://images.unsplash.com/photo-1414235077428-338989a2e8c0?auto=format&fit=crop&w=1200&q=80')" }}
                    />
                    <div className="p-6 space-y-4">
                        <h2 className="text-xl font-black text-slate-900">Parser behavior</h2>
                        <ul className="space-y-3 text-sm text-slate-600">
                            <li><strong className="text-slate-900">Header discovery:</strong> scans messy exports where the real table starts after metadata rows.</li>
                            <li><strong className="text-slate-900">Column inference:</strong> maps item, quantity, revenue, cost, and date fields using aliases and numeric fallbacks.</li>
                            <li><strong className="text-slate-900">Cleaning:</strong> strips currency symbols, commas, blanks, summary rows, and invalid records.</li>
                            <li><strong className="text-slate-900">Insights:</strong> updates dashboard, matrix, recommendations, and raw data automatically.</li>
                        </ul>
                    </div>
                </Card>
            </div>
        </div>
    );
}

function StatusPanel({ type, title, message, result }) {
    const success = type === 'success';
    const Icon = success ? CheckCircle2 : AlertCircle;
    const classes = success
        ? 'bg-emerald-50 border-emerald-200 text-emerald-800'
        : 'bg-red-50 border-red-200 text-red-800';

    return (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className={`mt-6 p-5 border rounded-lg flex items-start gap-3 shadow-sm ${classes}`}>
            <Icon className={`w-5 h-5 mt-0.5 shrink-0 ${success ? 'text-emerald-600' : 'text-red-600'}`} />
            <div className="w-full">
                <h3 className="text-sm font-bold">{title}</h3>
                <p className="text-sm mt-1 opacity-90">{message}</p>
                {result && (
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-4">
                        <MiniStat label="Rows" value={integer(result?.rows_ingested)} />
                        <MiniStat label="Rejected" value={integer(result?.rows_rejected)} />
                        <MiniStat label="Revenue" value={money(result?.total_revenue)} />
                        <MiniStat label="Units" value={integer(result?.total_units)} />
                    </div>
                )}
            </div>
        </motion.div>
    );
}

function MiniStat({ label, value }) {
    return (
        <div className="bg-white/70 rounded-md px-3 py-2 border border-white/70">
            <p className="text-[10px] uppercase tracking-widest opacity-60 font-bold">{label}</p>
            <p className="text-sm font-black">{value}</p>
        </div>
    );
}
