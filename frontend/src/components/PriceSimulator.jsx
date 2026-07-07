import { useMemo, useState } from 'react';
import { Calculator, ArrowRight } from 'lucide-react';

import { Card } from '../ui/Card';
import { asArray, decimal, integer, money, text, toNumber } from '../utils/format';

// How strongly demand reacts to a price change (price elasticity):
// %ΔQuantity = elasticity × %ΔPrice. Restaurant studies put most menu items
// between -0.5 and -1.5; the presets bracket that range.
const ELASTICITY_PRESETS = [
    { key: 'low', label: 'Loyal demand', value: -0.5, hint: 'Signature items guests order anyway' },
    { key: 'typical', label: 'Typical', value: -1.0, hint: 'Most menu items' },
    { key: 'high', label: 'Price-sensitive', value: -1.5, hint: 'Commodity items with easy substitutes' },
];

export function PriceSimulator({ classifications }) {
    const items = useMemo(
        () => asArray(classifications)
            .filter((c) => toNumber(c?.total_quantity) > 0)
            .sort((a, b) => toNumber(b?.total_revenue) - toNumber(a?.total_revenue)),
        [classifications],
    );

    const [selectedName, setSelectedName] = useState('');
    const [pricePct, setPricePct] = useState(5);
    const [elasticityKey, setElasticityKey] = useState('typical');

    const item = items.find((c) => c?.item_name === selectedName) || items[0];
    if (!item) return null;

    const elasticity = (ELASTICITY_PRESETS.find((p) => p.key === elasticityKey) || ELASTICITY_PRESETS[1]).value;

    const qty = toNumber(item.total_quantity);
    const revenue = toNumber(item.total_revenue);
    const unitCost = toNumber(item.unit_cost);
    const unitPrice = qty > 0 ? revenue / qty : 0;
    const currentProfit = (unitPrice - unitCost) * qty;

    const priceFactor = 1 + pricePct / 100;
    const demandFactor = Math.max(0, 1 + elasticity * (pricePct / 100));
    const newPrice = unitPrice * priceFactor;
    const newQty = qty * demandFactor;
    const newRevenue = newPrice * newQty;
    const newProfit = (newPrice - unitCost) * newQty;

    const profitDelta = newProfit - currentProfit;
    const revenueDelta = newRevenue - revenue;

    return (
        <Card className="p-6 border-slate-200">
            <div className="flex items-center gap-2 mb-1">
                <Calculator className="w-4 h-4 text-primary-600" />
                <h3 className="text-sm font-bold text-slate-800 uppercase tracking-widest">Price Simulator</h3>
            </div>
            <p className="text-xs text-slate-400 font-semibold mb-5">
                What-if: change an item&apos;s price and project the impact over the same period, assuming demand reacts to price.
            </p>

            <div className="grid grid-cols-1 lg:grid-cols-[1fr_1.2fr] gap-6">
                <div className="space-y-4">
                    <div>
                        <label className="block text-[10px] font-bold uppercase tracking-widest text-slate-400 mb-1">Menu item</label>
                        <select
                            value={item.item_name}
                            onChange={(e) => setSelectedName(e.target.value)}
                            className="w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm font-semibold text-slate-700 shadow-sm focus:border-primary-400 focus:outline-none focus:ring-1 focus:ring-primary-300"
                        >
                            {items.map((c) => (
                                <option key={text(c?.item_name)} value={c?.item_name}>{text(c?.item_name)}</option>
                            ))}
                        </select>
                    </div>

                    <div>
                        <label className="block text-[10px] font-bold uppercase tracking-widest text-slate-400 mb-1">
                            Price change: <span className={`${pricePct >= 0 ? 'text-emerald-700' : 'text-red-700'}`}>{pricePct > 0 ? '+' : ''}{pricePct}%</span>
                        </label>
                        <input
                            type="range" min={-20} max={20} step={1} value={pricePct}
                            onChange={(e) => setPricePct(Number(e.target.value))}
                            className="w-full accent-primary-600"
                        />
                        <div className="flex justify-between text-[10px] font-semibold text-slate-400"><span>-20%</span><span>0</span><span>+20%</span></div>
                    </div>

                    <div>
                        <label className="block text-[10px] font-bold uppercase tracking-widest text-slate-400 mb-1.5">Demand sensitivity</label>
                        <div className="flex gap-2">
                            {ELASTICITY_PRESETS.map((preset) => (
                                <button
                                    key={preset.key}
                                    onClick={() => setElasticityKey(preset.key)}
                                    title={preset.hint}
                                    className={`flex-1 rounded-md border px-2 py-2 text-xs font-bold transition-colors ${
                                        elasticityKey === preset.key
                                            ? 'bg-ink-900 text-white border-ink-900'
                                            : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'
                                    }`}
                                >
                                    {preset.label}
                                </button>
                            ))}
                        </div>
                    </div>
                </div>

                <div className="rounded-lg border border-slate-200 bg-slate-50/60 p-5">
                    <div className="grid grid-cols-[1fr_auto_1fr] items-center gap-3 text-sm">
                        <div className="space-y-3">
                            <SimStat label="Price" value={money(unitPrice)} />
                            <SimStat label="Units (period)" value={integer(qty)} />
                            <SimStat label="Revenue" value={money(revenue)} />
                            <SimStat label="Gross profit" value={money(currentProfit)} />
                        </div>
                        <ArrowRight className="w-5 h-5 text-slate-300" />
                        <div className="space-y-3">
                            <SimStat label="New price" value={money(newPrice)} accent />
                            <SimStat label="Projected units" value={integer(newQty)} accent />
                            <SimStat label="Projected revenue" value={money(newRevenue)} accent />
                            <SimStat label="Projected profit" value={money(newProfit)} accent />
                        </div>
                    </div>
                    <div className={`mt-5 rounded-md border px-4 py-3 text-sm font-bold ${
                        profitDelta >= 0 ? 'bg-emerald-50 border-emerald-200 text-emerald-800' : 'bg-red-50 border-red-200 text-red-800'
                    }`}>
                        Profit impact: {profitDelta >= 0 ? '+' : ''}{money(profitDelta)}
                        <span className="font-semibold opacity-80"> · Revenue {revenueDelta >= 0 ? '+' : ''}{money(revenueDelta)} · assumes {decimal(Math.abs(elasticity), 1)}% demand drop per 1% price rise</span>
                    </div>
                    <p className="text-[11px] text-slate-400 font-medium mt-3">
                        A directional estimate, not a forecast — real demand response depends on competition, guest mix, and menu presentation. Test price changes on a small window first.
                    </p>
                </div>
            </div>
        </Card>
    );
}

function SimStat({ label, value, accent = false }) {
    return (
        <div className="flex items-baseline justify-between gap-3">
            <span className="text-[10px] font-bold uppercase tracking-widest text-slate-400">{label}</span>
            <span className={`font-black tabular-nums ${accent ? 'text-primary-700' : 'text-slate-800'}`}>{value}</span>
        </div>
    );
}
