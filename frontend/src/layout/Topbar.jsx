import { useAuth } from '../hooks/useAuth';
import { LogOut, User, Menu } from 'lucide-react';

export const Topbar = ({ toggleSidebar }) => {
    const { user, logout } = useAuth();
    
    return (
        <header className="h-16 bg-white border-b border-slate-200 flex items-center justify-between px-4 md:px-8 sticky top-0 z-20 w-full transition-all">
            <button 
                className="md:hidden p-2 -ml-2 text-slate-500 hover:text-slate-800 hover:bg-slate-100 rounded-lg transition-colors"
                onClick={toggleSidebar}
            >
                <Menu className="w-5 h-5" />
            </button>
            <div className="flex items-center gap-4 ml-auto">
                <div className="text-right hidden sm:block">
                    <p className="text-sm font-semibold text-slate-700">{user?.email || 'Admin User'}</p>
                    <p className="text-xs text-slate-500">MenuMind Administrator</p>
                </div>
                <div className="w-9 h-9 bg-primary-50 rounded-full flex items-center justify-center border border-primary-100 shrink-0 shadow-sm">
                    <User className="w-5 h-5 text-primary-600" />
                </div>
                <div className="w-px h-6 bg-slate-200 mx-2"></div>
                <button 
                    onClick={logout}
                    className="flex items-center gap-2 text-sm font-medium text-slate-500 hover:text-red-600 transition-colors"
                >
                    <LogOut className="w-4 h-4" />
                    <span className="hidden sm:inline">Logout</span>
                </button>
            </div>
        </header>
    );
};
