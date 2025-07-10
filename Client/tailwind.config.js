/** @type {import('tailwindcss').Config} */
module.exports = {
    darkMode: 'class',
    content: ["./src/**/*.{js,jsx,ts,tsx}"],
    theme: {
        extend: {
            screens: {
                'smaller': {'max': '355px'},
            },
            colors: {
                mirage: {
                    '50': '#f4f6fb',
                    '100': '#e8ecf6',
                    '200': '#cbd8ec',
                    '300': '#9db6dc',
                    '400': '#6990c7',
                    '500': '#4672b1',
                    '600': '#345995',
                    '700': '#2b4779',
                    '800': '#273e65',
                    '900': '#253555',
                    '950': '#111827',
                },
            },
        },
    },
    plugins: [],
};
