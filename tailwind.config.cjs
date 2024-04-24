const daisyui = require('daisyui');
const typography = require('@tailwindcss/typography');
const forms = require('@tailwindcss/forms');

/** @type {import('tailwindcss').Config}*/
const config = {
	content: ['./src/**/*.{html,js,svelte,ts}'],

	theme: {
		extend: {}
	},

	plugins: [forms, typography, daisyui],

	daisyui: {
		themes: [
			{
				mytheme: {
					primary: '#00ADB5',
					secondary: '#5b21b6',
					accent: '#EEEEEE',
					neutral: '#393E46',
					'base-100': '#222831',
					info: '#1d4ed8',
					success: '#059669',
					warning: '#f59e0b',
					error: '#dc2626'
				}
			}
		]
	}
};

module.exports = config;
