import { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { AlertCircle, CalendarCheck, Download, Printer, TrendingUp } from 'lucide-react';

import api from '../services/api';
import { useActiveRestaurant } from '../hooks/useActiveRestaurant';
import { Card } from '../ui/Card';
import { EmptyState } from '../ui/EmptyState';
import { Skeleton } from '../ui/Skeleton';
import { asArray, dateLabel, decimal, getErrorMessage, integer, money, text, toNumber } from '../utils/format';

export default function MonthlyReport() {
    const activeRestaurant = useActiveRestaurant();
    const [searchParams, setSearchParams] = useSearchParams();
    const [months, setMonths] = useState([]);
    const [report, setReport] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    // '' = current month (1st -> today)
    const selectedMonth = searchParams.get('month') || '';

    useEffect(() => {
        const fetchReport = async () => {
            if (!activeRestaurant) {
                setReport(null);
                setMonths([]);
                setLoading(false);
                return;
            }
            setLoading(true);
            try {
                const params = new URLSearchParams({ restaurant_name: activeRestaurant });
                if (selectedMonth) params.set('month', selectedMonth);
                const [reportRes, monthsRes] = await Promise.all([
                    api.get(`/analytics/monthly-report?${params.toString()}`),
                    api.get(`/analytics/months?restaurant_name=${encodeURIComponent(activeRestaurant)}`),
                ]);
                setReport(reportRes.data && typeof reportRes.data === 'object' ? reportRes.data : null);
                setMonths(asArray(monthsRes.data));
                setError(null);
            } catch (err) {
                setError(getErrorMessage(err, 'Failed to load the monthly report.'));
            } finally {
                setLoading(false);
            }
        };
        fetchReport();
    }, [activeRestaurant, selectedMonth]);

    const summary = report?.summary;
    const items = asArray(report?.items);

    const changeMonth = (value) => {
        if (value) setSearchParams({ month: value });
        else setSearchParams({});
    };

    const exportCsv = () => {
        const quote = (v) => `"${String(v ?? '').replace(/"/g, '""')}"`;
        const header = ['Item', 'Category', 'Units', 'Revenue', 'Profit', 'Margin %'];
        const rows = items.map((i) => [
            quote(text(i?.item_name, '')), quote(text(i?.category, '')),
            toNumber(i?.total_quantity), toNumber(i?.total_revenue).toFixed(2),
            toNumber(i?.total_profit).toFixed(2), toNumber(i?.profit_margin).toFixed(1),
        ]);
        rows.push([quote('TOTAL'), '', summary?.total_units ?? 0,
            toNumber(summary?.total_revenue).toFixed(2), toNumber(summary?.total_profit).toFixed(2), '']);
        const csv = [header.map(quote), ...rows].map((r) => r.join(',')).join('\n');
        const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `${activeRestaurant}_report_${text(summary?.month, 'month')}.csv`
            .replace(/[\\/:*?"<>|]/g, '-').replace(/\s+/g, '_');
        link.click();
        URL.revokeObjectURL(url);
    };

    return (
        <div className="space-y-7">
            <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between print:hidden">
                <div className="flex items-center gap-4">
                    <div className="w-12 h-12 bg-ink-900 rounded-lg shadow-sm flex items-center justify-center">
                        <CalendarCheck className="w-6 h-6 text-primary-100" />
                    </div>
                    <div>
                        <p className="text-xs font-bold uppercase tracking-[0.24em] text-primary-700">Month in review</p>
                        <h1 className="text-3xl font-black text-slate-900 tracking-tight mt-1">Monthly Report</h1>
                        <p className="text-slate-500 text-sm mt-1">
                            Item-wise totals for a full month — or the running month from the 1st through today.
                        </p>
                    </div>
                </div>

                <div className="flex items-end gap-3">
                    <div>
                        <label className="block text-[10px] font-bold uppercase tracking-widest text-slate-400 mb-1">Month</label>
                        <select
                            value={selectedMonth}
                            onChange={(e) => changeMonth(e.target.value)}
                            className="rounded-md border border-slate-200 bg-white px-3 py-2 text-sm font-semibold text-slate-700 shadow-sm focus:border-primary-400 focus:outline-none focus:ring-1 focus:ring-primary-300"
                        >
                            <option value="">Current month (1st → today)</option>
                            {months.map((m) => <option key={m} value={m}>{monthLabel(m)}</option>)}
                        </select>
                    </div>
                    <button onClick={exportCsv} disabled={!items.length}
                        className="inline-flex items-center gap-1.5 rounded-md border border-slate-200 bg-white px-3 py-2 text-sm font-semibold text-slate-600 shadow-sm hover:bg-slate-50 disabled:opacity-40">
                        <Download className="w-4 h-4" /> CSV
                    </button>
                    <button onClick={() => window.print()} disabled={!items.length}
                        className="inline-flex items-center gap-1.5 rounded-md border border-slate-200 bg-white px-3 py-2 text-sm font-semibold text-slate-600 shadow-sm hover:bg-slate-50 disabled:opacity-40">
                        <Printer className="w-4 h-4" /> Print
                    </button>
                </div>
            </div>

            {error ? (
                <div className="p-5 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3 shadow-sm">
                    <AlertCircle className="w-5 h-5 text-red-500 mt-0.5 shrink-0" />
                    <p className="text-sm text-red-700 font-semibold">{error}</p>
                </div>
            ) : !activeRestaurant ? (
                <EmptyState title="No restaurant selected" message="Upload sales data first to generate monthly reports." />
            ) : loading ? (
                <div className="space-y-5">
                    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                        {[1, 2, 3, 4].map((i) => <Skeleton key={i} className="h-24 w-full rounded-lg" />)}
                    </div>
                    <Skeleton className="h-64 w-full rounded-lg" />
                </div>
            ) : !summary || items.length === 0 ? (
                <EmptyState message="No sales recorded in this month." />
            ) : (
                <>
                    <Card className="p-6 border-slate-200">
                        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 mb-5">
                            <div>
                                <h2 className="text-xl font-black text-slate-900">{text(summary.label)}</h2>
                                <p className="text-xs font-semibold text-slate-400 mt-0.5">
                                    {dateLabel(summary.start_date)} → {dateLabel(summary.end_date)}
                                    {summary.is_partial && (
                                        <span className="ml-2 inline-block text-[10px] font-bold uppercase tracking-wider text-amber-700 bg-amber-50 border border-amber-200 rounded px-1.5 py-0.5">
                                            Month in progress — totals so far
                                        </span>
                                    )}
                                </p>
                            </div>
                            <p className="text-xs font-semibold text-slate-400">
                                {integer(summary.days_recorded)} day(s) recorded · {integer(summary.item_count)} item(s)
                            </p>
                        </div>

                        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                            <ReportStat label="Total Revenue" value={money(summary.total_revenue)} />
                            <ReportStat label="Estimated Profit" value={money(summary.total_profit)} accent />
                            <ReportStat label="Units Sold" value={integer(summary.total_units)} />
                            <ReportStat label="Top Item" value={text(summary.top_item, '—')} />
                        </div>

                        {summary.best_day && (
                            <p className="text-xs font-semibold text-slate-500 mt-4 flex items-center gap-1.5">
                                <TrendingUp className="w-3.5 h-3.5 text-primary-600" />
                                Best day: {dateLabel(summary.best_day.date)} — {money(summary.best_day.total_revenue)} revenue,
                                {' '}{integer(summary.best_day.total_quantity)} units.
                            </p>
                        )}
                    </Card>

                    <Card className="overflow-hidden border-slate-200">
                        <div className="overflow-x-auto">
                            <table className="w-full text-sm text-left text-slate-800">
                                <thead className="text-xs text-slate-500 uppercase bg-slate-50 border-b border-slate-100 font-semibold tracking-wider">
                                    <tr>
                                        <th className="px-6 py-4">#</th>
                                        <th className="px-6 py-4">Item</th>
                                        <th className="px-6 py-4 text-center">Category</th>
                                        <th className="px-6 py-4 text-right">Units</th>
                                        <th className="px-6 py-4 text-right">Revenue</th>
                                        <th className="px-6 py-4 text-right">Profit</th>
                                        <th className="px-6 py-4 text-right">Margin %</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-slate-100/60">
                                    {items.map((item, index) => (
                                        <tr key={`${text(item?.item_name)}-${index}`} className="hover:bg-slate-50/50">
                                            <td className="px-6 py-3.5 text-xs font-mono text-slate-400">{index + 1}</td>
                                            <td className="px-6 py-3.5 font-bold text-slate-700">
                                                {text(item?.item_name, 'Unnamed')}
                                                {item?.item_type === 'combo' && (
                                                    <span title="Set menu / buffet" className="ml-1.5 inline-block align-middle text-[9px] font-bold uppercase tracking-wider text-purple-700 bg-purple-50 border border-purple-200 rounded px-1 py-0.5">
                                                        Buffet
                                                    </span>
                                                )}
                                            </td>
                                            <td className="px-6 py-3.5 text-center">
                                                <span className={`inline-flex px-2 py-0.5 rounded-md text-xs font-bold ring-1 ring-inset ${categoryClasses(item?.category)}`}>
                                                    {text(item?.category, '—')}
                                                </span>
                                            </td>
                                            <td className="px-6 py-3.5 text-right tabular-nums font-semibold">{integer(item?.total_quantity)}</td>
                                            <td className="px-6 py-3.5 text-right tabular-nums">{money(item?.total_revenue)}</td>
                                            <td className="px-6 py-3.5 text-right tabular-nums font-bold text-emerald-700">{money(item?.total_profit)}</td>
                                            <td className="px-6 py-3.5 text-right tabular-nums">{decimal(item?.profit_margin, 1)}%</td>
                                        </tr>
                                    ))}
                                </tbody>
                                <tfoot>
                                    <tr className="border-t-2 border-slate-200 font-bold text-slate-900 bg-slate-50/60">
                                        <td className="px-6 py-3.5" colSpan={3}>TOTAL — {text(summary.label)}{summary.is_partial ? ' (so far)' : ''}</td>
                                        <td className="px-6 py-3.5 text-right tabular-nums">{integer(summary.total_units)}</td>
                                        <td className="px-6 py-3.5 text-right tabular-nums">{money(summary.total_revenue)}</td>
                                        <td className="px-6 py-3.5 text-right tabular-nums text-emerald-700">{money(summary.total_profit)}</td>
                                        <td className="px-6 py-3.5" />
                                    </tr>
                                </tfoot>
                            </table>
                        </div>
                    </Card>
                </>
            )}
        </div>
    );
}

function ReportStat({ label, value, accent = false }) {
    return (
        <div className={`rounded-lg border p-4 ${accent ? 'bg-emerald-50/70 border-emerald-200' : 'bg-slate-50/70 border-slate-200'}`}>
            <p className="text-[10px] font-bold uppercase tracking-widest text-slate-400">{label}</p>
            <p className={`text-xl font-black tabular-nums mt-1 truncate ${accent ? 'text-emerald-800' : 'text-slate-900'}`} title={String(value)}>{value}</p>
        </div>
    );
}

function categoryClasses(category) {
    switch (category) {
        case 'Star': return 'text-emerald-700 bg-emerald-50 ring-emerald-600/20';
        case 'Plowhorse': return 'text-yellow-700 bg-yellow-50 ring-yellow-600/20';
        case 'Puzzle': return 'text-blue-700 bg-blue-50 ring-blue-600/20';
        case 'Dog': return 'text-red-700 bg-red-50 ring-red-600/20';
        default: return 'text-slate-700 bg-slate-50 ring-slate-600/20';
    }
}

function monthLabel(key) {
    const [year, month] = String(key).split('-').map(Number);
    if (!year || !month) return key;
    return new Date(year, month - 1, 1).toLocaleDateString(undefined, { month: 'long', year: 'numeric' });
}
