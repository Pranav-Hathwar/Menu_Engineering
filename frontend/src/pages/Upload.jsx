import { useState } from 'react';
import { Card } from '../ui/Card';
import { Button } from '../ui/Button';
import { UploadCloud, File, AlertCircle, CheckCircle2 } from 'lucide-react';
import api from '../services/api';
import { motion } from 'framer-motion';

export default function Upload() {
    const [file, setFile] = useState(null);
    const [restaurantName, setRestaurantName] = useState('');
    const [loading, setLoading] = useState(false);
    const [status, setStatus] = useState(null); // 'success', 'error'
    const [message, setMessage] = useState('');

    const handleFileChange = (e) => {
        if (e.target.files && e.target.files[0]) {
            setFile(e.target.files[0]);
            setStatus(null);
            setMessage('');
        }
    };

    const handleUpload = async () => {
        if (!file || !restaurantName.trim()) return;
        setLoading(true);
        setStatus(null);
        
        const formData = new FormData();
        formData.append('file', file);
        formData.append('restaurant_name', restaurantName.trim());

        try {
            const response = await api.post('/upload', formData);
            setStatus('success');
            setMessage(response.data.message || 'File processed successfully. Navigate to Overview to view results.');
            setFile(null);
            setRestaurantName('');
            
            // Dispatch event to organically trigger topbar dropdown to refetch
            window.dispatchEvent(new Event('restaurantUploaded'));
        } catch (error) {
            setStatus('error');
            setMessage(error.response?.data?.detail || 'Failed to process file. Ensure it contains the standard item_name, quantity, and price columns.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="space-y-8">
            <div>
                <h1 className="text-2xl font-bold text-slate-800 tracking-tight">Data Input Hub</h1>
                <p className="text-slate-500 text-sm mt-1">Upload unstructured restaurant sales logs (CSV or Excel) for deterministic classification.</p>
            </div>

            <Card className="max-w-2xl p-8 border-slate-200">
                <div className="mb-6">
                    <label className="block text-sm font-bold text-slate-700 mb-2">Restaurant / Hotel Name <span className="text-red-500">*</span></label>
                    <input 
                        type="text" 
                        placeholder="e.g. Mint Masala" 
                        value={restaurantName}
                        onChange={(e) => setRestaurantName(e.target.value)}
                        className="w-full px-4 py-3 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500 text-slate-800 transition-shadow bg-slate-50 focus:bg-white"
                        required
                    />
                </div>

                <div 
                    className="border-2 border-dashed border-slate-300 rounded-2xl p-10 flex flex-col items-center justify-center bg-slate-50 text-center hover:bg-slate-100 transition-colors relative"
                >
                    <input 
                        type="file" 
                        accept=".csv, application/vnd.openxmlformats-officedocument.spreadsheetml.sheet, application/vnd.ms-excel"
                        onChange={handleFileChange}
                        className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                    />
                    
                    <div className="w-16 h-16 bg-white rounded-full flex items-center justify-center shadow-sm mb-4 border border-slate-100">
                        <UploadCloud className="w-8 h-8 text-primary-500" />
                    </div>
                    <h3 className="text-lg font-bold text-slate-800">Select or drop your payload here</h3>
                    <p className="text-sm text-slate-500 mt-2 max-w-sm">
                        Accepts .CSV or .XLSX files targeting standard item string mapping, quantities, and operational costs securely.
                    </p>
                </div>

                {file && (
                    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="mt-6 p-4 bg-white border border-slate-200 rounded-xl flex items-center justify-between shadow-sm">
                        <div className="flex items-center gap-3 truncate">
                            <File className="w-5 h-5 text-primary-600 shrink-0" />
                            <span className="text-sm font-semibold text-slate-700 truncate">{file.name}</span>
                        </div>
                        <Button onClick={handleUpload} disabled={loading || !restaurantName.trim()} className="px-6 shrink-0 ml-4 font-semibold">
                            {loading ? 'Processing Pandas Logic...' : 'Execute Upload'}
                        </Button>
                    </motion.div>
                )}

                {status === 'success' && (
                    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="mt-6 p-5 bg-emerald-50 border border-emerald-200 rounded-xl flex items-start gap-3 shadow-sm">
                        <CheckCircle2 className="w-5 h-5 text-emerald-500 mt-0.5 shrink-0" />
                        <div>
                            <h3 className="text-sm font-bold text-emerald-800">Database Overwrite Complete</h3>
                            <p className="text-sm text-emerald-600 mt-1">{message}</p>
                        </div>
                    </motion.div>
                )}

                {status === 'error' && (
                    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="mt-6 p-5 bg-red-50 border border-red-200 rounded-xl flex items-start gap-3 shadow-sm">
                        <AlertCircle className="w-5 h-5 text-red-500 mt-0.5 shrink-0" />
                        <div>
                            <h3 className="text-sm font-bold text-red-800">Formatting Rejection</h3>
                            <p className="text-sm text-red-600 mt-1">{message}</p>
                        </div>
                    </motion.div>
                )}
            </Card>
        </div>
    );
}
