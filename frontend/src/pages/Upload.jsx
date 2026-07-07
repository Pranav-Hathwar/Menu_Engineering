import { useCallback, useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { AlertCircle, CheckCircle2, Copy, Database, File, Mail, RefreshCw, Trash2, UploadCloud } from 'lucide-react';

import api from '../services/api';
import { Button } from '../ui/Button';
import { Card } from '../ui/Card';
import { asArray, dateLabel, getErrorMessage, integer, money, text, toNumber } from '../utils/format';

export default function Upload() {
    const [file, setFile] = useState(null);
    const [restaurantName, setRestaurantName] = useState('');
    const [reportDate, setReportDate] = useState('');
    const [loading, setLoading] = useState(false);
    const [status, setStatus] = useState(null); // 'success' | 'error' | 'duplicate'
    const [message, setMessage] = useState('');
    const [result, setResult] = useState(null);

    const [batches, setBatches] = useState([]);
    const [batchesLoading, setBatchesLoading] = useState(true);
    const [deletingId, setDeletingId] = useState(null);

    const [ingest, setIngest] = useState(null);
    const [ingestRunning, setIngestRunning] = useState(false);
    const [ingestResult, setIngestResult] = useState(null);

    const fetchIngestStatus = useCallback(async () => {
        try {
            const res = await api.get('/ingest/status');
            setIngest(res.data && typeof res.data === 'object' ? res.data : null);
        } catch {
            setIngest(null);
        }
    }, []);

    useEffect(() => { fetchIngestStatus(); }, [fetchIngestStatus]);

    const checkInboxNow = async () => {
        setIngestRunning(true);
        setIngestResult(null);
        try {
            const res = await api.post('/ingest/run');
            setIngestResult(res.data);
            await Promise.all([fetchIngestStatus(), fetchBatches()]);
            window.dispatchEvent(new Event('restaurantUploaded'));
        } catch (error) {
            setIngestResult({ ok: false, detail: getErrorMessage(error, 'Inbox check failed.') });
        } finally {
            setIngestRunning(false);
        }
    };

    const fetchBatches = useCallback(async () => {
        setBatchesLoading(true);
        try {
            const response = await api.get('/upload/batches');
            setBatches(asArray(response.data));
        } catch {
            setBatches([]);
        } finally {
            setBatchesLoading(false);
        }
    }, []);

    useEffect(() => { fetchBatches(); }, [fetchBatches]);

    const handleFileChange = (e) => {
        if (e.target.files && e.target.files[0]) {
            setFile(e.target.files[0]);
            setStatus(null);
            setMessage('');
            setResult(null);
        }
    };

    const handleUpload = async (allowDuplicate = false) => {
        if (!file || !restaurantName.trim()) return;
        setLoading(true);
        setStatus(null);

        const formData = new FormData();
        formData.append('file', file);
        formData.append('restaurant_name', restaurantName.trim());
        if (reportDate) formData.append('report_date', reportDate);
        if (allowDuplicate) formData.append('allow_duplicate', 'true');

        try {
            const response = await api.post('/upload', formData);
            setStatus('success');
            setResult(response.data);
            setMessage(response.data.message || 'File processed successfully.');
            setFile(null);
            setRestaurantName('');
            setReportDate('');
            window.dispatchEvent(new Event('restaurantUploaded'));
            fetchBatches();
        } catch (error) {
            setResult(null);
            if (error?.response?.status === 409) {
                // Duplicate file — keep the selection so the user can override.
                setStatus('duplicate');
                setMessage(getErrorMessage(error, 'This file was already uploaded to this restaurant.'));
            } else {
                setStatus('error');
                setMessage(getErrorMessage(error, 'Failed to process file. Upload CSV, Excel, or JSON with item, quantity, revenue, and optional cost/date fields.'));
            }
        } finally {
            setLoading(false);
        }
    };

    const handleDelete = async (batchId) => {
        setDeletingId(batchId);
        try {
            await api.delete(`/upload/batches/${batchId}`);
            await fetchBatches();
            window.dispatchEvent(new Event('restaurantUploaded'));
        } catch (error) {
            setStatus('error');
            setMessage(getErrorMessage(error, 'Failed to delete this upload batch.'));
        } finally {
            setDeletingId(null);
        }
    };

    return (
        <div className="space-y-7">
            <div>
                <p className="text-xs font-bold uppercase tracking-[0.24em] text-primary-700">Ingestion pipeline</p>
                <h1 className="text-3xl font-black text-slate-900 tracking-tight mt-2">Data Input Hub</h1>
                <p className="text-slate-500 text-sm mt-2 max-w-2xl">
                    Upload CSV, Excel, or JSON sales exports. The parser detects headers, cleans values, normalizes rows, and rejects unusable records. Identical re-uploads are blocked to prevent double-counting.
                </p>
            </div>

            <div className="grid grid-cols-1 xl:grid-cols-[1.15fr_0.85fr] gap-6">
                <Card className="p-6 sm:p-8 border-slate-200">
                    <div className="mb-6 grid grid-cols-1 sm:grid-cols-[1.5fr_1fr] gap-4">
                        <div>
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
                        <div>
                            <label className="block text-sm font-bold text-slate-700 mb-2">Report Date <span className="text-slate-400 font-semibold">(optional)</span></label>
                            <input
                                type="date"
                                value={reportDate}
                                onChange={(e) => setReportDate(e.target.value)}
                                className="w-full px-4 py-3 rounded-md border border-slate-200 focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500 text-slate-900 transition-shadow bg-white"
                            />
                            <p className="text-[11px] text-slate-400 font-medium mt-1.5">
                                Used when the file has no date column — e.g. a daily report that only says which day it covers in its name.
                            </p>
                        </div>
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
                            <Button onClick={() => handleUpload(false)} disabled={loading || !restaurantName.trim()} className="px-6 shrink-0 font-semibold">
                                {loading ? 'Normalizing data...' : 'Process Upload'}
                            </Button>
                        </motion.div>
                    )}

                    {status === 'success' && (
                        <StatusPanel type="success" title="Ingestion Complete" message={message} result={result} />
                    )}

                    {status === 'duplicate' && (
                        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="mt-6 p-5 border rounded-lg flex items-start gap-3 shadow-sm bg-amber-50 border-amber-200 text-amber-900">
                            <Copy className="w-5 h-5 mt-0.5 shrink-0 text-amber-600" />
                            <div className="w-full">
                                <h3 className="text-sm font-bold">Duplicate file detected</h3>
                                <p className="text-sm mt-1 opacity-90">{message}</p>
                                <div className="flex gap-3 mt-4">
                                    <Button onClick={() => handleUpload(true)} disabled={loading} className="px-4 py-2 text-sm bg-amber-600 hover:bg-amber-700">
                                        {loading ? 'Uploading...' : 'Upload anyway'}
                                    </Button>
                                    <button onClick={() => { setStatus(null); setFile(null); }} className="px-4 py-2 text-sm font-semibold text-amber-800 hover:underline">
                                        Cancel
                                    </button>
                                </div>
                            </div>
                        </motion.div>
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
                            <li><strong className="text-slate-900">De-duplication:</strong> an identical file can't be ingested twice into the same restaurant unless you explicitly override.</li>
                        </ul>
                    </div>
                </Card>
            </div>

            <Card className="p-6 border-slate-200">
                <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                    <div className="flex items-start gap-3 min-w-0">
                        <div className={`w-10 h-10 rounded-md flex items-center justify-center shrink-0 ${ingest?.enabled && ingest?.configured ? 'bg-emerald-50 border border-emerald-200' : 'bg-slate-100 border border-slate-200'}`}>
                            <Mail className={`w-5 h-5 ${ingest?.enabled && ingest?.configured ? 'text-emerald-600' : 'text-slate-400'}`} />
                        </div>
                        <div className="min-w-0">
                            <div className="flex items-center gap-2 flex-wrap">
                                <h2 className="text-sm font-bold text-slate-800 uppercase tracking-widest">Email Auto-Ingestion</h2>
                                <span className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-md border ${
                                    ingest?.enabled && ingest?.configured
                                        ? 'text-emerald-700 bg-emerald-50 border-emerald-200'
                                        : 'text-slate-500 bg-slate-50 border-slate-200'
                                }`}>
                                    {ingest?.enabled && ingest?.configured ? 'Active' : 'Not configured'}
                                </span>
                            </div>
                            <p className="text-xs text-slate-500 font-medium mt-1 truncate">
                                Inbox: <span className="font-bold text-slate-700">{text(ingest?.inbox)}</span>
                                {' '}· Restaurant: <span className="font-bold text-slate-700">{text(ingest?.restaurant_name)}</span>
                                {ingest?.enabled && ` · checks every ${text(ingest?.poll_minutes)} min`}
                            </p>
                            <p className="text-xs text-slate-400 font-medium mt-0.5">
                                Last check: {ingest?.last_check ? dateLabel(ingest.last_check) : 'never'} — {text(ingest?.last_result)}
                            </p>
                        </div>
                    </div>
                    <button
                        onClick={checkInboxNow}
                        disabled={ingestRunning}
                        className="shrink-0 inline-flex items-center gap-1.5 rounded-md bg-ink-900 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-ink-800 disabled:opacity-40"
                    >
                        <RefreshCw className={`w-4 h-4 ${ingestRunning ? 'animate-spin' : ''}`} />
                        {ingestRunning ? 'Checking inbox…' : 'Check inbox now'}
                    </button>
                </div>
                {ingestResult && (
                    <div className={`mt-4 rounded-md border px-4 py-2.5 text-sm font-semibold ${ingestResult.ok ? 'bg-emerald-50 border-emerald-200 text-emerald-800' : 'bg-amber-50 border-amber-200 text-amber-900'}`}>
                        {text(ingestResult.detail)}
                        {asArray(ingestResult.details).map((line, index) => (
                            <p key={index} className="text-xs font-medium opacity-80 mt-1">{line}</p>
                        ))}
                    </div>
                )}
            </Card>

            <Card className="p-6 sm:p-8 border-slate-200">
                <div className="flex items-center justify-between mb-5">
                    <div className="flex items-center gap-2">
                        <Database className="w-4 h-4 text-primary-600" />
                        <h2 className="text-sm font-bold text-slate-800 uppercase tracking-widest">Uploaded Batches</h2>
                        <span className="text-xs font-semibold text-slate-400">({batches.length})</span>
                    </div>
                    <button onClick={fetchBatches} className="flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-slate-800">
                        <RefreshCw className={`w-3.5 h-3.5 ${batchesLoading ? 'animate-spin' : ''}`} /> Refresh
                    </button>
                </div>

                {batchesLoading ? (
                    <p className="text-sm text-slate-400 py-6 text-center">Loading batches…</p>
                ) : batches.length === 0 ? (
                    <p className="text-sm text-slate-400 py-6 text-center">No uploads yet. Ingest a file above to get started.</p>
                ) : (
                    <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                            <thead>
                                <tr className="border-b border-slate-200 text-left text-xs font-bold uppercase tracking-widest text-slate-400">
                                    <th className="py-2.5 pr-4">Restaurant</th>
                                    <th className="py-2.5 px-4">File</th>
                                    <th className="py-2.5 px-4">Uploaded</th>
                                    <th className="py-2.5 px-4 text-right">Rows</th>
                                    <th className="py-2.5 px-4 text-right">Revenue</th>
                                    <th className="py-2.5 pl-4 text-right">Action</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-100">
                                {batches.map((b) => (
                                    <tr key={text(b?.batch_id)} className="text-slate-700 hover:bg-slate-50">
                                        <td className="py-2.5 pr-4 font-semibold text-slate-900">{text(b?.restaurant_name)}</td>
                                        <td className="py-2.5 px-4 max-w-[200px] truncate" title={text(b?.filename)}>{text(b?.filename)}</td>
                                        <td className="py-2.5 px-4">{dateLabel(b?.created_at)}</td>
                                        <td className="py-2.5 px-4 text-right tabular-nums">{integer(b?.row_count)}</td>
                                        <td className="py-2.5 px-4 text-right tabular-nums">{money(b?.total_revenue)}</td>
                                        <td className="py-2.5 pl-4 text-right">
                                            <button
                                                onClick={() => handleDelete(b?.batch_id)}
                                                disabled={deletingId === b?.batch_id}
                                                className="inline-flex items-center gap-1.5 text-xs font-semibold text-red-600 hover:text-red-800 disabled:opacity-50"
                                            >
                                                <Trash2 className="w-3.5 h-3.5" />
                                                {deletingId === b?.batch_id ? 'Deleting…' : 'Delete'}
                                            </button>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </Card>
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
                    <>
                        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-4">
                            <MiniStat label="Rows" value={integer(result?.rows_ingested)} />
                            <MiniStat label="Rejected" value={integer(result?.rows_rejected)} />
                            <MiniStat label="Revenue" value={money(result?.total_revenue)} />
                            <MiniStat label="Units" value={integer(result?.total_units)} />
                        </div>
                        {toNumber(result?.dates_defaulted) > 0 && (
                            <p className="text-xs mt-3 font-semibold opacity-80">
                                Note: {integer(result?.dates_defaulted)} row(s) had unreadable dates and were assigned the file&apos;s most common date.
                            </p>
                        )}
                        {result?.date_mode && result.date_mode !== 'column' && result?.applied_date && (
                            <p className="text-xs mt-2 font-semibold opacity-80">
                                {result.date_mode === 'provided' && `The file has no date column — all rows were dated ${dateLabel(result.applied_date)} (the report date you entered).`}
                                {result.date_mode === 'detected' && `The file has no date column — all rows were dated ${dateLabel(result.applied_date)} (detected from the file name/title).`}
                                {result.date_mode === 'email-date' && `The file has no date column — all rows were dated ${dateLabel(result.applied_date)} (the email's sent date).`}
                                {result.date_mode === 'upload-day' && `⚠ The file has no date column, so all rows were dated today (${dateLabel(result.applied_date)}). If this report is for another day, delete this batch and re-upload with the Report Date field set.`}
                            </p>
                        )}
                    </>
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
