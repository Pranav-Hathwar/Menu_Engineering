import { NavLink } from 'react-router-dom';
import { LayoutDashboard, UploadCloud, PieChart, Utensils } from 'lucide-react';

export const Sidebar = ({ isOpen, setIsOpen }) => {
    const navItems = [
        { path: '/', label: 'Overview', icon: LayoutDashboard },
        { path: '/upload', label: 'Data Input', icon: UploadCloud },
        { path: '/insights', label: 'AI Analytics', icon: PieChart },
        { path: '/menu', label: 'Catalog', icon: Utensils },
    ];

    return (
        <aside className={`fixed inset-y-0 left-0 z-40 w-64 bg-white border-r border-slate-200 min-h-screen flex flex-col transform transition-transform duration-300 ease-in-out md:relative md:translate-x-0 ${isOpen ? 'translate-x-0' : '-translate-x-full'}`}>
            <div className="p-6">
                <h1 className="text-xl font-bold text-slate-800 tracking-tighter flex items-center gap-2">
                    <PieChart className="w-6 h-6 text-primary-500" />
                    MenuMind<span className="font-medium text-slate-400">AI</span>
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
                                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${
                                    isActive 
                                    ? 'bg-primary-50 text-primary-700' 
                                    : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
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
                <div className="px-4 py-3 bg-slate-50 rounded-xl border border-slate-100">
                    <p className="text-xs text-slate-500 font-medium">Workspace</p>
                    <p className="text-sm font-semibold text-slate-700">Premium Owner</p>
                </div>
            </div>
        </aside>
    );
};
