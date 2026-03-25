export const Table = ({ headers, rows, className = "" }) => {
    return (
        <div className={`w-full overflow-x-auto rounded-xl border border-slate-200 ${className}`}>
            <table className="w-full text-left border-collapse">
                <thead>
                    <tr className="border-b border-slate-200 bg-slate-50">
                        {headers.map((h, i) => (
                            <th key={i} className="px-5 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                                {h}
                            </th>
                        ))}
                    </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 bg-white">
                    {rows.map((row, i) => (
                        <tr key={i} className="hover:bg-slate-50/50 transition-colors">
                            {row.map((cell, j) => (
                                <td key={j} className="px-5 py-4 text-sm text-slate-700">
                                    {cell}
                                </td>
                            ))}
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
};
