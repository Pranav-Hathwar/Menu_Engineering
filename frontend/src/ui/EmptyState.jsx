import { FileQuestion } from 'lucide-react';
import { motion } from 'framer-motion';

export const EmptyState = ({
    title = "No data available",
    description,
    message = "Upload your sales data to begin.",
}) => {
    return (
        <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="w-full flex flex-col items-center justify-center p-12 text-center border border-dashed border-slate-300 rounded-lg bg-white/80 shadow-sm"
        >
            <div className="w-14 h-14 bg-primary-50 rounded-md flex items-center justify-center mb-5 border border-primary-100">
                <FileQuestion className="w-7 h-7 text-primary-600" />
            </div>
            <h3 className="text-xl font-bold text-slate-900 tracking-tight">{title}</h3>
            <p className="text-sm text-slate-500 mt-2 max-w-sm">{description || message}</p>
        </motion.div>
    );
};
