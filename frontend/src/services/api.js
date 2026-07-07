import axios from 'axios';

// Vite handles proxying /api to localhost:8000 safely in dev mode.
const api = axios.create({
    baseURL: '/api',
});

// Interceptor intelligently attaches the user's JWT standardly
api.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('token');
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => Promise.reject(error)
);

api.interceptors.response.use(
    (response) => response,
    (error) => {
        const status = error.response?.status;
        const url = error.config?.url || '';
        // A 401 from login/register just means bad credentials — let the form
        // show the message. Hard-redirecting here would reload the page and
        // wipe the error before the user could read it.
        const isCredentialCall = url.includes('/auth/login') || url.includes('/auth/register');
        if (status === 401 && !isCredentialCall) {
            localStorage.removeItem('token');
            if (window.location.pathname !== '/login') {
                window.location.href = '/login';
            }
        }
        return Promise.reject(error);
    }
);

export default api;
