import { Card } from '../ui/Card';
import { Badge } from '../ui/Badge';
import { HelpCircle, BrainCircuit, BarChart3, UploadCloud, Target, Sparkles, Server } from 'lucide-react';

export default function About() {
    return (
        <div className="space-y-8 max-w-4xl mx-auto pb-12">
            <div className="text-center space-y-4">
                <div className="w-16 h-16 bg-primary-50 rounded-2xl mx-auto flex items-center justify-center border border-primary-100 shadow-sm">
                    <BrainCircuit className="w-8 h-8 text-primary-600" />
                </div>
                <h1 className="text-4xl font-extrabold text-slate-800 tracking-tight">How MenuMind AI Works</h1>
                <p className="text-slate-500 text-lg max-w-2xl mx-auto">
                    The autonomous intelligence layer transforming raw, unstructured restaurant data into actionable menu engineering strategies.
                </p>
            </div>

            <Card className="p-8 border-slate-200 shadow-sm mt-8 space-y-6">
                <div className="flex items-center gap-3 border-b border-slate-100 pb-4">
                    <Target className="w-6 h-6 text-primary-600" />
                    <h2 className="text-2xl font-bold text-slate-800">The BCG Matrix Algorithm</h2>
                </div>
                <p className="text-slate-600 leading-relaxed">
                    MenuMind AI evaluates every item on your menu using the universally acclaimed <strong>Boston Consulting Group (BCG) Menu Engineering Matrix</strong>. We mathematically score items based on two primary dimensions: <strong>Popularity</strong> (unit volume sold) and <strong>Profitability</strong> (unit revenue generated).
                </p>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
                    <div className="p-5 bg-emerald-50 rounded-xl border border-emerald-100">
                        <div className="flex items-center gap-2 mb-2">
                            <Badge className="bg-emerald-100 text-emerald-800">Stars</Badge>
                        </div>
                        <p className="text-sm text-emerald-700"><strong>High Popularity & High Profit.</strong> Your flagship items. Keep quality high and feature them prominently.</p>
                    </div>
                    <div className="p-5 bg-yellow-50 rounded-xl border border-yellow-100">
                        <div className="flex items-center gap-2 mb-2">
                            <Badge className="bg-yellow-100 text-yellow-800">Plowhorses</Badge>
                        </div>
                        <p className="text-sm text-yellow-700"><strong>High Popularity & Low Profit.</strong> Your traffic drivers. Consider slight price increases or reducing portion costs.</p>
                    </div>
                    <div className="p-5 bg-blue-50 rounded-xl border border-blue-100">
                        <div className="flex items-center gap-2 mb-2">
                            <Badge className="bg-blue-100 text-blue-800">Puzzles</Badge>
                        </div>
                        <p className="text-sm text-blue-700"><strong>Low Popularity & High Profit.</strong> Highly profitable, but hard to sell. Decrease prices slightly or rename/reposition them.</p>
                    </div>
                    <div className="p-5 bg-red-50 rounded-xl border border-red-100">
                        <div className="flex items-center gap-2 mb-2">
                            <Badge className="bg-red-100 text-red-800">Dogs</Badge>
                        </div>
                        <p className="text-sm text-red-700"><strong>Low Popularity & Low Profit.</strong> Underperformers. Consider removing them from the menu completely.</p>
                    </div>
                </div>
            </Card>

            <Card className="p-8 border-slate-200 shadow-sm space-y-6">
                <div className="flex items-center gap-3 border-b border-slate-100 pb-4">
                    <Server className="w-6 h-6 text-primary-600" />
                    <h2 className="text-2xl font-bold text-slate-800">Ultra-Resilient Data Ingestion</h2>
                </div>
                <div className="flex gap-6 items-start">
                    <div className="w-12 h-12 shrink-0 bg-slate-50 rounded-full flex items-center justify-center border border-slate-200">
                        <UploadCloud className="w-6 h-6 text-slate-600" />
                    </div>
                    <div>
                        <h3 className="text-lg font-bold text-slate-800 mb-2">No formatting required. Just upload.</h3>
                        <p className="text-slate-600 leading-relaxed text-sm">
                            Our proprietary Python Pandas parsing engine uses heuristic layout-scanning to organically extract tabular data from horribly formatted files. It automatically skips generic POS metadata rows, ignores blank cells, and strips currency symbols.
                            <br /><br />
                            If your file doesn't have headers, the Engine dynamically derives meaning simply by scanning column data types (e.g. tracking standard text blobs as Items, integers as Quantities, and decimal vectors as Revenue)!
                        </p>
                    </div>
                </div>
            </Card>

            <Card className="p-8 border-slate-200 shadow-sm space-y-6">
                <div className="flex items-center gap-3 border-b border-slate-100 pb-4">
                    <Sparkles className="w-6 h-6 text-primary-600" />
                    <h2 className="text-2xl font-bold text-slate-800">Multi-Tenant Analytics</h2>
                </div>
                <div className="flex gap-6 items-start">
                    <div className="w-12 h-12 shrink-0 bg-slate-50 rounded-full flex items-center justify-center border border-slate-200">
                        <BarChart3 className="w-6 h-6 text-slate-600" />
                    </div>
                    <div>
                        <h3 className="text-lg font-bold text-slate-800 mb-2">Scalable Database Architecture</h3>
                        <p className="text-slate-600 leading-relaxed text-sm">
                            MenuMind allows you to upload arrays of data across entirely distinct Restaurant entities! Our backend cleanly maps these datasets relationally to unique context IDs. The global unified Dropdown on your Topbar allows you to effortlessly shift computational focus across different establishments natively, filtering down dashboards in real-time.
                        </p>
                    </div>
                </div>
            </Card>
        </div>
    );
}
