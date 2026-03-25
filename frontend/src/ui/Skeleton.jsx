export const Skeleton = ({ className = "" }) => {
    return (
        <div className={`animate-pulse bg-slate-200/70 rounded-lg ${className}`}></div>
    );
};
