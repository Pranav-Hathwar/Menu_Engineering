import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { Topbar } from './Topbar';
import { motion } from 'framer-motion';
import { useState } from 'react';

export default function DashboardLayout() {
    const [sidebarOpen, setSidebarOpen] = useState(false);

    return (
        <div className="flex min-h-screen bg-background text-slate-800 font-sans">
            <Sidebar isOpen={sidebarOpen} setIsOpen={setSidebarOpen} />
            <div className="flex-1 flex flex-col min-w-0">
                <Topbar toggleSidebar={() => setSidebarOpen(!sidebarOpen)} />
                <main className="flex-1 p-4 sm:p-8 overflow-y-auto isolate flex flex-col min-h-0">
                    <div className="flex-1">
                        <motion.div
                            initial={{ opacity: 0, y: 15 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ duration: 0.4, ease: "easeOut" }}
                            className="max-w-6xl mx-auto w-full"
                        >
                            <Outlet />
                        </motion.div>
                    </div>
                    
                    {/* Global Developer Embedded Brand */}
                    <footer className="w-full max-w-6xl mx-auto mt-16 pt-6 pb-2 border-t border-slate-100 text-center shrink-0">
                        <p className="text-sm font-medium text-slate-500 opacity-90">
                            Developed by <a href="https://github.com/Pranav-Hathwar" target="_blank" rel="noopener noreferrer" className="font-bold text-primary-600 hover:text-primary-700 hover:underline transition-all">Pranav Hathwar</a>
                        </p>
                    </footer>
                </main>
            </div>
            
            {/* Mobile Overlay Mask */}
            {sidebarOpen && (
                <div 
                    className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-30 md:hidden transition-opacity" 
                    onClick={() => setSidebarOpen(false)}
                />
            )}
        </div>
    );
};
