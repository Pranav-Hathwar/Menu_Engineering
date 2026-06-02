import { motion } from 'framer-motion';
import { asArray, decimal, integer, text } from '../utils/format';

const containerVariants = {
    hidden: { opacity: 0 },
    show: {
        opacity: 1,
        transition: { staggerChildren: 0.05 }
    }
};

const itemVariants = {
    hidden: { opacity: 0, scale: 0.95, y: 10 },
    show: { opacity: 1, scale: 1, y: 0 }
};

const Quadrant = ({ title, description, colorClass, items }) => (
    <div className={`p-5 rounded-lg border ${colorClass.border} ${colorClass.bg} flex flex-col h-[420px] overflow-y-auto shadow-sm`}>
        <div className="mb-4 sticky top-0 z-10 pb-2 bg-transparent backdrop-blur-sm">
            <h3 className={`text-lg font-black tracking-tight ${colorClass.text}`}>{title}</h3>
            <p className="text-xs text-slate-500 font-medium mt-0.5">{description}</p>
        </div>
        <motion.div
            className="space-y-3 flex-1"
            variants={containerVariants}
            initial="hidden"
            animate="show"
        >
            {items.map((item, index) => (
                <motion.div
                    key={`${text(item?.item_name, 'item')}-${index}`}
                    variants={itemVariants}
                    whileHover={{ scale: 1.01 }}
                    className="p-4 bg-white rounded-md shadow-sm border border-slate-100 flex justify-between items-center cursor-pointer transition-all hover:shadow-md hover:border-slate-300 group"
                >
                    <span className="font-bold text-slate-800 text-sm truncate mr-3 group-hover:text-primary-700 transition-colors" title={text(item?.item_name, 'Unnamed item')}>
                        {text(item?.item_name, 'Unnamed item')}
                    </span>
                    <div className="text-right shrink-0 bg-slate-50 px-2 py-1 rounded-md border border-slate-100">
                        <span className="block text-[11px] font-medium text-slate-500 uppercase tracking-widest mb-0.5">
                            Qty: <span className="text-slate-700 font-bold">{integer(item?.total_quantity)}</span>
                        </span>
                        <span className={`block text-xs font-bold ${colorClass.text}`}>Unit Profit: Rs {decimal(item?.profit)}</span>
                    </div>
                </motion.div>
            ))}
            {items.length === 0 && (
                <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="h-full flex items-center justify-center text-sm text-slate-400 font-medium"
                >
                    No items placed here
                </motion.div>
            )}
        </motion.div>
    </div>
);

export const MenuMatrix = ({ classifications = [] }) => {
    const safe = asArray(classifications);
    const stars = safe.filter(c => c?.category === "Star");
    const plowhorses = safe.filter(c => c?.category === "Plowhorse");
    const puzzles = safe.filter(c => c?.category === "Puzzle");
    const dogs = safe.filter(c => c?.category === "Dog");

    return (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5 w-full max-w-full">
            <Quadrant
                title="Stars"
                description="High popularity, high profitability"
                colorClass={{ bg: 'bg-emerald-50/70', border: 'border-emerald-100', text: 'text-emerald-700' }}
                items={stars}
            />
            <Quadrant
                title="Plowhorses"
                description="High popularity, lower profitability"
                colorClass={{ bg: 'bg-yellow-50/70', border: 'border-yellow-100', text: 'text-yellow-700' }}
                items={plowhorses}
            />
            <Quadrant
                title="Puzzles"
                description="Low popularity, high profitability"
                colorClass={{ bg: 'bg-blue-50/70', border: 'border-blue-100', text: 'text-blue-700' }}
                items={puzzles}
            />
            <Quadrant
                title="Dogs"
                description="Low popularity, low profitability"
                colorClass={{ bg: 'bg-red-50/70', border: 'border-red-100', text: 'text-red-700' }}
                items={dogs}
            />
        </div>
    );
};
