import { FileQuestion } from 'lucide-react';
import { motion } from 'framer-motion';

export const EmptyState = ({ title = "No data available", description = "Upload your sales data to begin." }) => {
    return (
        <motion.div 
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="w-full flex flex-col items-center justify-center p-16 text-center border-2 border-dashed border-slate-200 rounded-2xl bg-white shadow-sm"
        >
            <div className="w-16 h-16 bg-slate-50 rounded-full flex items-center justify-center mb-5 border border-slate-100">
                <FileQuestion className="w-8 h-8 text-primary-400" />
            </div>
            <h3 className="text-xl font-bold text-slate-800 tracking-tight">{title}</h3>
            <p className="text-sm text-slate-500 mt-2 max-w-sm">{description}</p>
        </motion.div>
    );
};
