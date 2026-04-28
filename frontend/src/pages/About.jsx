import { BarChart3, BrainCircuit, Server, Target, UploadCloud } from 'lucide-react';

import { Badge } from '../ui/Badge';
import { Card } from '../ui/Card';

export default function About() {
    return (
        <div className="space-y-7 max-w-5xl mx-auto pb-12">
            <section className="relative overflow-hidden rounded-lg border border-white/70 bg-ink-900 text-white shadow-soft">
                <div
                    className="absolute inset-0 opacity-25 bg-cover bg-center"
                    style={{ backgroundImage: "url('https://images.unsplash.com/photo-1559339352-11d035aa65de?auto=format&fit=crop&w=1400&q=80')" }}
                />
                <div className="absolute inset-0 bg-gradient-to-r from-ink-900 via-ink-900/85 to-primary-700/45" />
                <div className="relative p-8">
                    <BrainCircuit className="w-9 h-9 text-primary-100" />
                    <h1 className="text-4xl font-black tracking-tight mt-5">How MenuMind Pro Works</h1>
                    <p className="text-white/75 text-base max-w-2xl mt-3">
                        A deterministic analytics workspace that converts messy restaurant sales exports into menu-engineering decisions.
                    </p>
                </div>
            </section>

            <Card className="p-7 border-slate-200 shadow-sm space-y-5">
                <div className="flex items-center gap-3 border-b border-slate-100 pb-4">
                    <Target className="w-6 h-6 text-primary-700" />
                    <h2 className="text-2xl font-black text-slate-900">Menu Engineering Matrix</h2>
                </div>
                <p className="text-slate-600 leading-relaxed">
                    Items are classified by popularity and estimated per-unit profitability. This keeps the decision logic explainable and auditable.
                </p>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <Category badge="Stars" text="High popularity and high profitability. Protect quality and feature these items." className="bg-emerald-50 border-emerald-100 text-emerald-800" />
                    <Category badge="Plowhorses" text="High popularity with weaker margins. Tune price, portion, or cost structure carefully." className="bg-yellow-50 border-yellow-100 text-yellow-800" />
                    <Category badge="Puzzles" text="Strong margin with weak demand. Improve naming, placement, and staff prompts." className="bg-blue-50 border-blue-100 text-blue-800" />
                    <Category badge="Dogs" text="Low demand and low margin. Rework, bundle, or remove if there is no strategic reason to keep them." className="bg-red-50 border-red-100 text-red-800" />
                </div>
            </Card>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
                <InfoCard
                    icon={UploadCloud}
                    title="Resilient Data Ingestion"
                    text="The backend reads CSV, Excel, and JSON files, discovers headers, maps columns, cleans currency and number formats, rejects invalid rows, and stores normalized sales records."
                />
                <InfoCard
                    icon={BarChart3}
                    title="Operational Insights"
                    text="The analytics layer calculates revenue drivers, estimated profit, category mix, margin watchlists, and trend signals for the selected restaurant."
                />
                <InfoCard
                    icon={Server}
                    title="Authenticated Workspace"
                    text="Routes are protected by JWT authentication and sales data is scoped to the authenticated owner for new uploads and records."
                />
                <InfoCard
                    icon={BrainCircuit}
                    title="Explainable Recommendations"
                    text="Recommendations are rule-based rather than black-box. Each item receives a clear category, action, reason, priority, and confidence score."
                />
            </div>
        </div>
    );
}

function Category({ badge, text, className }) {
    return (
        <div className={`p-5 rounded-lg border ${className}`}>
            <Badge className="bg-white/70 text-inherit border-white/70">{badge}</Badge>
            <p className="text-sm mt-3 font-medium leading-relaxed">{text}</p>
        </div>
    );
}

function InfoCard({ icon: Icon, title, text }) {
    return (
        <Card className="p-7 border-slate-200 shadow-sm">
            <Icon className="w-7 h-7 text-primary-700" />
            <h3 className="text-xl font-black text-slate-900 mt-4">{title}</h3>
            <p className="text-sm text-slate-600 leading-relaxed mt-2">{text}</p>
        </Card>
    );
}
