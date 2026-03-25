import { useState, useEffect } from 'react';

export function useActiveRestaurant() {
    const [restaurant, setRestaurant] = useState(localStorage.getItem('activeRestaurant') || '');

    useEffect(() => {
        const handleStorageChange = () => {
            setRestaurant(localStorage.getItem('activeRestaurant') || '');
        };
        
        window.addEventListener('restaurantChanged', handleStorageChange);
        // Bind natively to upload completion to auto-update
        window.addEventListener('restaurantUploaded', handleStorageChange);
        
        return () => {
            window.removeEventListener('restaurantChanged', handleStorageChange);
            window.removeEventListener('restaurantUploaded', handleStorageChange);
        }
    }, []);

    return restaurant;
}
