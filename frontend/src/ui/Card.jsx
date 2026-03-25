import { motion } from 'framer-motion';

export const Card = ({ children, className = "", animate = true, hover = false }) => {
    const baseClasses = `bg-white rounded-2xl shadow-soft border border-slate-200/60 overflow-hidden ${className}`;
    
    // Fallback static version if animations disabled
    if (!animate && !hover) {
        return <div className={baseClasses}>{children}</div>;
    }

    return (
        <motion.div 
            className={baseClasses}
            initial={animate ? { opacity: 0, y: 15 } : false}
            animate={animate ? { opacity: 1, y: 0 } : false}
            transition={{ duration: 0.4, ease: "easeOut" }}
            whileHover={hover ? { y: -3, transition: { duration: 0.2 } } : {}}
        >
            {children}
        </motion.div>
    );
};
