/** @type {import('tailwindcss').Config} */
module.exports = {
    content: [
        // Include all HTML files in your templates directory
        './templates/**/*.html',

        // Include any JavaScript files that might use Tailwind classes
        './static/js/**/*.js',

        // If you use components stored elsewhere, include their paths
        './static/components/**/*.html',
        './static/components/**/*.js',
    ],
    theme: {
        extend: {},
    },
    plugins: [],
};
