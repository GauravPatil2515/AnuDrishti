import { useState, useEffect } from 'react';

/**
 * Custom hook for dark mode with pink-purple theme
 * Automatically detects system preference and persists user choice
 */
export const useDarkMode = () => {
    const [darkMode, setDarkMode] = useState(() => {
        // Check localStorage first
        const saved = localStorage.getItem('darkMode');
        if (saved !== null) {
            return saved === 'true';
        }
        // Fall back to system preference
        return window.matchMedia('(prefers-color-scheme: dark)').matches;
    });

    useEffect(() => {
        const root = document.documentElement;

        if (darkMode) {
            root.classList.add('dark');
        } else {
            root.classList.remove('dark');
        }

        localStorage.setItem('darkMode', darkMode.toString());
    }, [darkMode]);

    const toggleDarkMode = () => setDarkMode(prev => !prev);

    return { darkMode, setDarkMode, toggleDarkMode };
};
