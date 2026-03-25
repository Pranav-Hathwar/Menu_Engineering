export const Badge = ({ children, type = "default", className = "" }) => {
    const types = {
        default: "bg-slate-100 text-slate-700 border-slate-200",
        Star: "bg-yellow-50 text-yellow-700 border-yellow-200",
        Plowhorse: "bg-blue-50 text-blue-700 border-blue-200",
        Puzzle: "bg-fuchsia-50 text-fuchsia-700 border-fuchsia-200",
        Dog: "bg-slate-100 text-slate-500 border-slate-200",
        High: "bg-red-50 text-red-700 border-red-200",
        Medium: "bg-orange-50 text-orange-700 border-orange-200",
        Low: "bg-green-50 text-green-700 border-green-200",
    };

    return (
        <span className={`px-2.5 py-0.5 rounded-full text-xs font-medium border ${types[type] || types.default} ${className}`}>
            {children}
        </span>
    );
};
