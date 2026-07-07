import { useAuth } from '../hooks/useAuth';
import { LogOut, User, Menu, Store } from 'lucide-react';
import { useState, useEffect } from 'react';
import api from '../services/api';
import { asArray } from '../utils/format';

export const Topbar = ({ toggleSidebar }) => {
    const { user, logout } = useAuth();
    const [restaurants, setRestaurants] = useState([]);
    const [active, setActive] = useState(localStorage.getItem('activeRestaurant') || '');

    const fetchRestaurants = async () => {
        try {
            const res = await api.get('/analytics/restaurants');
            const list = asArray(res.data).filter(Boolean);
            setRestaurants(list);

            // Reconcile the stored selection with reality: pick the first
            // restaurant when nothing is selected OR the selected one no
            // longer exists (e.g. its last upload batch was deleted).
            const stored = localStorage.getItem('activeRestaurant') || '';
            if (list.length === 0) {
                if (stored) {
                    localStorage.removeItem('activeRestaurant');
                    setActive('');
                    window.dispatchEvent(new Event('restaurantChanged'));
                }
            } else if (!stored || !list.includes(stored)) {
                const first = list[0];
                localStorage.setItem('activeRestaurant', first);
                setActive(first);
                window.dispatchEvent(new Event('restaurantChanged'));
            }
        } catch (e) {
            console.error("Failed to load restaurants:", e);
        }
    };

    useEffect(() => {
        fetchRestaurants();
        // Refresh dropdown on explicit file upload
        window.addEventListener('restaurantUploaded', fetchRestaurants);
        return () => window.removeEventListener('restaurantUploaded', fetchRestaurants);
    }, []);

    const handleSelectChange = (e) => {
        const val = e.target.value;
        setActive(val);
        localStorage.setItem('activeRestaurant', val);
        window.dispatchEvent(new Event('restaurantChanged'));
    };
    
    return (
        <header className="h-16 glass-panel border-b border-white/70 flex items-center justify-between px-4 md:px-8 sticky top-0 z-20 w-full transition-all">
            <button 
                className="md:hidden p-2 -ml-2 text-slate-500 hover:text-slate-800 hover:bg-slate-100 rounded-lg transition-colors"
                onClick={toggleSidebar}
            >
                <Menu className="w-5 h-5" />
            </button>
            <div className="flex items-center gap-4 ml-auto">
                
                {/* Global Multi-Tenant Navigator Form */}
                <div className="flex items-center gap-2 bg-white border border-slate-200 px-3 py-1.5 rounded-md shrink-0 shadow-sm">
                    <Store className="w-4 h-4 text-slate-400" />
                    <select 
                        className="bg-transparent border-none text-sm font-bold text-slate-700 outline-none w-32 cursor-pointer appearance-none truncate"
                        value={active}
                        onChange={handleSelectChange}
                    >
                        {restaurants.length === 0 && <option value="">No Data</option>}
                        {restaurants.map((r) => (
                            <option key={r} value={r}>{r}</option>
                        ))}
                    </select>
                </div>

                <div className="w-px h-6 bg-slate-200 mx-2 hidden sm:block"></div>

                <div className="text-right hidden sm:block">
                    <p className="text-sm font-semibold text-slate-700">{user?.email || 'Admin User'}</p>
                    <p className="text-xs text-slate-500">MenuMind Administrator</p>
                </div>
                <div className="w-9 h-9 bg-ink-900 rounded-md items-center justify-center border border-ink-900 shrink-0 shadow-sm hidden sm:flex">
                    <User className="w-5 h-5 text-primary-100" />
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
