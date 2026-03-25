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

// Graceful standard token expiration handling
api.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response && error.response.status === 401) {
            localStorage.removeItem('token');
            // Forcefully return to login if JWT expires mimicking enterprise layouts
            window.location.href = '/login';
        }
        return Promise.reject(error);
    }
);

export default api;
