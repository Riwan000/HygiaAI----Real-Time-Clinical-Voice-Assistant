/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class', // Enable class-based dark mode
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Clinical NeoTech Theme Colors
        primary: '#2563EB',           // Medical Blue - Primary buttons, links, icons
        primaryDark: '#1E3A8A',       // Deep Navy - Headers, nav bars
        accent: '#8B5CF6',            // Qdrant Purple - Secondary buttons, tags, AI elements
        accentLight: '#C4B5FD',       // Soft Violet - Highlights, hover states
        background: '#FFFFFF',         // Pure White - Backgrounds
        slate: '#64748B',             // Slate Gray - Secondary text, subheaders
        charcoal: '#0F172A',          // Charcoal - Main text, headlines
      },
      backgroundImage: {
        'gradient-clinical': 'linear-gradient(to right, #2563EB, #8B5CF6)',
        'gradient-discovery': 'linear-gradient(to right, #1E3A8A, #C4B5FD)',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        heading: ['Inter', 'Poppins', 'system-ui', 'sans-serif'],
        body: ['Inter', 'Roboto', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
    },
  },
  plugins: [],
}

