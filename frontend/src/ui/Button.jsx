import { motion } from 'framer-motion';

export const Button = ({ children, variant = "primary", className = "", ...props }) => {
    const variants = {
        primary: "bg-ink-900 text-white hover:bg-primary-700 shadow-sm border border-transparent",
        secondary: "bg-white text-slate-700 hover:bg-slate-50 border border-slate-200 shadow-sm",
        danger: "bg-red-50 text-red-700 hover:bg-red-100 border border-red-100"
    };

    return (
        <motion.button
            whileHover={{ scale: props.disabled ? 1 : 1.01 }}
            whileTap={{ scale: props.disabled ? 1 : 0.98 }}
            className={`px-4 py-2 rounded-md font-semibold transition-colors duration-200 outline-none focus:ring-2 focus:ring-primary-500/50 disabled:opacity-50 disabled:cursor-not-allowed ${variants[variant]} ${className}`}
            {...props}
        >
            {children}
        </motion.button>
    );
};
