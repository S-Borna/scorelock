/** @type {import('tailwindcss').Config} */
module.exports = {
    content: [
        "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
        "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
        "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
    ],
    theme: {
        extend: {
            colors: {
                scorelock: {
                    50: "#edfff4",
                    100: "#d5ffe6",
                    200: "#aefdcf",
                    300: "#70f5ab",
                    400: "#2de87f",
                    500: "#09ce5f",
                    600: "#01ab4c",
                    700: "#05863f",
                    800: "#0a6935",
                    900: "#0a562d",
                    950: "#003018",
                },
                surface: {
                    DEFAULT: "#0b0f1a",
                    50: "#f5f6fa",
                    100: "#ebedf3",
                    200: "#d2d6e5",
                    300: "#abb3cf",
                    400: "#7e8bb4",
                    500: "#5e6d9b",
                    600: "#4a5681",
                    700: "#3d4769",
                    800: "#1a2035",
                    900: "#111627",
                    950: "#0b0f1a",
                },
                accent: {
                    blue: "#3b82f6",
                    purple: "#8b5cf6",
                    amber: "#f59e0b",
                    rose: "#f43f5e",
                    cyan: "#06b6d4",
                },
            },
            fontFamily: {
                sans: ["var(--font-sans)", "system-ui", "-apple-system", "sans-serif"],
                display: ["var(--font-display)", "Georgia", "serif"],
                mono: ["var(--font-mono)", "JetBrains Mono", "monospace"],
            },
            fontSize: {
                "display-xl": ["3.75rem", { lineHeight: "1", letterSpacing: "-0.02em", fontWeight: "800" }],
                "display-lg": ["3rem", { lineHeight: "1.1", letterSpacing: "-0.02em", fontWeight: "700" }],
                "display-md": ["2.25rem", { lineHeight: "1.15", letterSpacing: "-0.01em", fontWeight: "700" }],
                "display-sm": ["1.875rem", { lineHeight: "1.2", letterSpacing: "-0.01em", fontWeight: "600" }],
            },
            backgroundImage: {
                "gradient-radial": "radial-gradient(var(--tw-gradient-stops))",
                "gradient-mesh": "radial-gradient(at 40% 20%, rgba(9,206,95,0.08) 0px, transparent 50%), radial-gradient(at 80% 0%, rgba(59,130,246,0.06) 0px, transparent 50%), radial-gradient(at 0% 50%, rgba(139,92,246,0.05) 0px, transparent 50%)",
                "glow-green": "radial-gradient(ellipse at center, rgba(9,206,95,0.15) 0%, transparent 70%)",
                "glow-blue": "radial-gradient(ellipse at center, rgba(59,130,246,0.12) 0%, transparent 70%)",
            },
            boxShadow: {
                "glow-sm": "0 0 15px -3px rgba(9,206,95,0.15)",
                "glow-md": "0 0 30px -5px rgba(9,206,95,0.2)",
                "glow-lg": "0 0 50px -10px rgba(9,206,95,0.25)",
                "inner-glow": "inset 0 1px 0 0 rgba(255,255,255,0.05)",
                "card": "0 1px 3px rgba(0,0,0,0.3), 0 0 0 1px rgba(255,255,255,0.03)",
                "card-hover": "0 8px 30px rgba(0,0,0,0.4), 0 0 0 1px rgba(9,206,95,0.1)",
                "elevated": "0 20px 60px -15px rgba(0,0,0,0.5)",
            },
            borderRadius: {
                "2xl": "1rem",
                "3xl": "1.5rem",
            },
            animation: {
                "fade-in": "fadeIn 0.5s ease-out",
                "fade-up": "fadeUp 0.6s ease-out",
                "slide-in": "slideIn 0.4s ease-out",
                "pulse-slow": "pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite",
                "shimmer": "shimmer 2s linear infinite",
                "glow": "glow 2s ease-in-out infinite alternate",
                "score-pop": "scorePop 0.3s cubic-bezier(0.68, -0.55, 0.265, 1.55)",
            },
            keyframes: {
                fadeIn: {
                    "0%": { opacity: "0" },
                    "100%": { opacity: "1" },
                },
                fadeUp: {
                    "0%": { opacity: "0", transform: "translateY(10px)" },
                    "100%": { opacity: "1", transform: "translateY(0)" },
                },
                slideIn: {
                    "0%": { opacity: "0", transform: "translateX(-10px)" },
                    "100%": { opacity: "1", transform: "translateX(0)" },
                },
                shimmer: {
                    "0%": { backgroundPosition: "-200% 0" },
                    "100%": { backgroundPosition: "200% 0" },
                },
                glow: {
                    "0%": { boxShadow: "0 0 5px rgba(9,206,95,0.1)" },
                    "100%": { boxShadow: "0 0 20px rgba(9,206,95,0.2)" },
                },
                scorePop: {
                    "0%": { transform: "scale(1)" },
                    "50%": { transform: "scale(1.2)" },
                    "100%": { transform: "scale(1)" },
                },
            },
            transitionTimingFunction: {
                "bounce-in": "cubic-bezier(0.68, -0.55, 0.265, 1.55)",
            },
        },
    },
    plugins: [],
};
