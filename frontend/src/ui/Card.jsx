import { motion } from 'framer-motion';

export const Card = ({ children, className = "", animate = true, hover = false }) => {
    const baseClasses = `bg-white/90 rounded-lg shadow-soft border border-white/70 overflow-hidden ring-1 ring-slate-900/5 ${className}`;

    if (!animate && !hover) {
        return <div className={baseClasses}>{children}</div>;
    }

    return (
        <motion.div
            className={baseClasses}
            initial={animate ? { opacity: 0, y: 12 } : false}
            animate={animate ? { opacity: 1, y: 0 } : false}
            transition={{ duration: 0.35, ease: "easeOut" }}
            whileHover={hover ? { y: -2, transition: { duration: 0.18 } } : {}}
        >
            {children}
        </motion.div>
    );
};
