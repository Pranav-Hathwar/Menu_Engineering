import { motion } from 'framer-motion';

export const Button = ({ children, variant = "primary", className = "", ...props }) => {
    const variants = {
        primary: "bg-primary-500 text-white hover:bg-primary-600 shadow-sm border border-transparent",
        secondary: "bg-white text-slate-700 hover:bg-slate-50 border border-slate-200 shadow-sm",
        danger: "bg-red-50 text-red-600 hover:bg-red-100 border border-red-100"
    };

    return (
        <motion.button 
            whileHover={{ scale: 1.01 }}
            whileTap={{ scale: 0.98 }}
            className={`px-4 py-2 rounded-lg font-medium transition-colors duration-200 outline-none focus:ring-2 focus:ring-primary-500/50 ${variants[variant]} ${className}`}
            {...props}
        >
            {children}
        </motion.button>
    );
};
