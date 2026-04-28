import { NavLink } from 'react-router-dom';
import { LayoutDashboard, UploadCloud, PieChart, Utensils, HelpCircle, Database } from 'lucide-react';

export const Sidebar = ({ isOpen, setIsOpen }) => {
    const navItems = [
        { path: '/', label: 'Overview', icon: LayoutDashboard },
        { path: '/upload', label: 'Data Input', icon: UploadCloud },
        { path: '/raw', label: 'Raw Data', icon: Database },
        { path: '/insights', label: 'Insights', icon: PieChart },
        { path: '/menu', label: 'Catalog', icon: Utensils },
        { path: '/about', label: 'How it Works', icon: HelpCircle },
    ];

    return (
        <aside className={`fixed inset-y-0 left-0 z-40 w-64 glass-panel border-r border-white/70 min-h-screen flex flex-col transform transition-transform duration-300 ease-in-out md:relative md:translate-x-0 ${isOpen ? 'translate-x-0' : '-translate-x-full'}`}>
            <div className="p-6">
                <h1 className="text-xl font-black text-slate-900 tracking-tight flex items-center gap-2">
                    <span className="w-9 h-9 rounded-md bg-ink-900 flex items-center justify-center">
                        <PieChart className="w-5 h-5 text-primary-100" />
                    </span>
                    MenuMind<span className="font-semibold text-primary-700">Pro</span>
                </h1>
            </div>
            
            <nav className="flex-1 px-4 py-2 space-y-1">
                {navItems.map((item) => {
                    const Icon = item.icon;
                    return (
                        <NavLink
                            key={item.path}
                            to={item.path}
                            className={({ isActive }) => 
                                `flex items-center gap-3 px-3 py-2.5 rounded-md text-sm font-semibold transition-all ${
                                    isActive 
                                    ? 'bg-ink-900 text-white shadow-sm' 
                                    : 'text-slate-600 hover:bg-white hover:text-slate-900'
                                }`
                            }
                        >
                            <Icon className="w-4 h-4" />
                            {item.label}
                        </NavLink>
                    );
                })}
            </nav>
            
            <div className="p-4 border-t border-slate-100">
                <div className="px-4 py-3 bg-white/80 rounded-lg border border-white/70">
                    <p className="text-xs text-slate-500 font-medium">Workspace</p>
                    <p className="text-sm font-semibold text-slate-700">Premium Owner</p>
                </div>
            </div>
        </aside>
    );
};
