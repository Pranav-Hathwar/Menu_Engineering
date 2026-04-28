import { useState, useEffect, createContext, useContext } from 'react';
import api from '../services/api';

const AuthContext = createContext();

function getAuthError(error, fallback) {
    const detail = error.response?.data?.detail;
    if (Array.isArray(detail)) {
        return detail.map((item) => item.msg).join(' ');
    }
    return detail || fallback;
}

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const verifySession = async () => {
            const token = localStorage.getItem('token');
            if (!token) {
                setLoading(false);
                return;
            }
            try {
                const res = await api.get('/auth/me');
                setUser(res.data);
            } catch (err) {
                localStorage.removeItem('token');
            } finally {
                setLoading(false);
            }
        };
        verifySession();
    }, []);

    const login = async (email, password) => {
        const formData = new URLSearchParams();
        formData.append('username', email.trim().toLowerCase());
        formData.append('password', password);

        try {
            const res = await api.post('/auth/login', formData);
            localStorage.setItem('token', res.data.access_token);
            const profile = await api.get('/auth/me');
            setUser(profile.data);
        } catch (error) {
            throw new Error(getAuthError(error, 'Invalid credentials. Check your email and password.'));
        }
    };

    const register = async (email, password) => {
        try {
            await api.post('/auth/register', { email: email.trim().toLowerCase(), password });
            await login(email, password);
        } catch (error) {
            throw new Error(getAuthError(error, 'Could not create your account.'));
        }
    };

    const logout = async () => {
        try {
            if (localStorage.getItem('token')) {
                await api.post('/auth/logout');
            }
        } catch (err) {
            // Client-side token removal is still the source of truth for stateless JWT logout.
        } finally {
            localStorage.removeItem('token');
            setUser(null);
        }
    };

    return (
        <AuthContext.Provider value={{ user, login, register, logout, loading }}>
            {children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => useContext(AuthContext);
