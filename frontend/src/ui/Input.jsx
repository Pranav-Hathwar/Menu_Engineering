export const Input = ({ label, className = "", ...props }) => {
    return (
        <div className={`flex flex-col gap-1.5 w-full ${className}`}>
            {label && <label className="text-sm font-medium text-slate-700">{label}</label>}
            <input 
                className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 bg-white text-slate-900 focus:outline-none focus:ring-4 focus:ring-primary-500/10 focus:border-primary-500 transition-all placeholder:text-slate-400 shadow-sm"
                {...props}
            />
        </div>
    );
};
