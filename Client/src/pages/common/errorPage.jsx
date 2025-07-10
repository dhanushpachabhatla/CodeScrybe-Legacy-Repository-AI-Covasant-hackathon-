import React from 'react';
import { Link } from 'react-router-dom';

const ErrorPage = () => {
    return (
        <div className="h-screen w-full flex items-center justify-center bg-mirage-50 dark:bg-mirage-900">
            <div className="text-center p-8">
                <img
                    src="/Owl-Error.png"
                    alt="Error"
                    className="mx-auto mb-6 max-w-xs w-full h-auto"
                />
                <h2 className="text-2xl font-bold text-mirage-700 dark:text-mirage-100 mb-4">
                    Oops! Page Not Found
                </h2>
            
                <p className="text-mirage-600 dark:text-mirage-400 mb-6">
                    The page you're looking for doesn't exist or has been moved.
                </p>
                <Link
                    to="/"
                    className="px-6 py-3 bg-mirage-600 dark:bg-mirage-400 text-white rounded-lg hover:bg-mirage-700 dark:hover:bg-mirage-300 transition-colors"
                >
                    Go to Home
                </Link>
            </div>
        </div>
    );
};

export default ErrorPage;