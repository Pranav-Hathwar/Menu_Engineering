import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './hooks/useAuth';
import { ErrorBoundary } from './components/ErrorBoundary';
import Login from './pages/Login';
import Signup from './pages/Signup';
import Dashboard from './pages/Dashboard';
import Upload from './pages/Upload';
import Insights from './pages/Insights';
import Catalog from './pages/Catalog';
import Recipes from './pages/Recipes';
import MonthlyReport from './pages/MonthlyReport';
import RawData from './pages/RawData';
import About from './pages/About';
import DashboardLayout from './layout/DashboardLayout';

const ProtectedRoute = ({ children }) => {
    const { user, loading } = useAuth();
    if (loading) return <div className="min-h-screen flex items-center justify-center">Loading...</div>;
    if (!user) return <Navigate to="/login" replace />;
    return children;
};

function AppRoutes() {
    return (
        <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/signup" element={<Signup />} />
            
            {/* Protected Route Group */}
            <Route path="/" element={
                <ProtectedRoute>
                    <DashboardLayout />
                </ProtectedRoute>
            }>
                <Route index element={<Dashboard />} />
                <Route path="upload" element={<Upload />} />
                <Route path="raw" element={<RawData />} />
                <Route path="insights" element={<Insights />} />
                <Route path="menu" element={<Catalog />} />
                <Route path="recipes" element={<Recipes />} />
                <Route path="report" element={<MonthlyReport />} />
                <Route path="about" element={<About />} />
            </Route>

            <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
    );
}

export default function App() {
    return (
        <ErrorBoundary>
            <AuthProvider>
                <BrowserRouter>
                    <AppRoutes />
                </BrowserRouter>
            </AuthProvider>
        </ErrorBoundary>
    );
}
