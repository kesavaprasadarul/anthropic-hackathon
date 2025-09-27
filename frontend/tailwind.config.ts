import type { Config } from "tailwindcss";

export default {
  darkMode: ["class"],
  content: ["./pages/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./app/**/*.{ts,tsx}", "./src/**/*.{ts,tsx}"],
  prefix: "",
  theme: {
    container: {
      center: true,
      padding: "2rem",
      screens: {
        "2xl": "1400px",
      },
    },
    extend: {
      colors: {
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        
        // Jarvis Theme Colors
        space: {
          dark: "hsl(var(--space-dark))",
          darker: "hsl(var(--space-darker))",
          light: "hsl(var(--space-light))",
        },
        neon: {
          cyan: "hsl(var(--neon-cyan))",
          blue: "hsl(var(--neon-blue))",
          magenta: "hsl(var(--neon-magenta))",
          teal: "hsl(var(--neon-teal))",
        },
        text: {
          primary: "hsl(var(--text-primary))",
          secondary: "hsl(var(--text-secondary))",
          tertiary: "hsl(var(--text-tertiary))",
        },
        sphere: {
          idle: "hsl(var(--sphere-idle))",
          listening: "hsl(var(--sphere-listening))",
          thinking: "hsl(var(--sphere-thinking))",
          speaking: "hsl(var(--sphere-speaking))",
        },
        
        // Standard shadcn colors mapped to Jarvis theme
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
        sidebar: {
          DEFAULT: "hsl(var(--sidebar-background))",
          foreground: "hsl(var(--sidebar-foreground))",
          primary: "hsl(var(--sidebar-primary))",
          "primary-foreground": "hsl(var(--sidebar-primary-foreground))",
          accent: "hsl(var(--sidebar-accent))",
          "accent-foreground": "hsl(var(--sidebar-accent-foreground))",
          border: "hsl(var(--sidebar-border))",
          ring: "hsl(var(--sidebar-ring))",
        },
        
        // Semantic colors
        success: "hsl(var(--success))",
        warning: "hsl(var(--warning))",
        error: "hsl(var(--error))",
      },
      
      // Jarvis gradients
      backgroundImage: {
        'gradient-space': 'var(--gradient-space)',
        'gradient-sphere': 'var(--gradient-sphere)',
        'gradient-neon': 'var(--gradient-neon)',
        'gradient-glow': 'var(--gradient-glow)',
      },
      
      // Jarvis shadows and effects
      boxShadow: {
        'neon': 'var(--shadow-neon)',
        'card': 'var(--shadow-card)',
        'sphere': 'var(--glow-sphere)',
      },
      
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
      keyframes: {
        "accordion-down": {
          from: {
            height: "0",
          },
          to: {
            height: "var(--radix-accordion-content-height)",
          },
        },
        "accordion-up": {
          from: {
            height: "var(--radix-accordion-content-height)",
          },
          to: {
            height: "0",
          },
        },
        // Jarvis sphere animations
        "sphere-float": {
          "0%, 100%": { transform: "translateY(0px) rotateY(0deg)" },
          "33%": { transform: "translateY(-10px) rotateY(120deg)" },
          "66%": { transform: "translateY(-5px) rotateY(240deg)" },
        },
        "sphere-pulse": {
          "0%, 100%": { transform: "scale(1)", opacity: "0.8" },
          "50%": { transform: "scale(1.05)", opacity: "1" },
        },
        "particle-orbit": {
          "0%": { transform: "rotate(0deg) translateX(50px) rotate(0deg)" },
          "100%": { transform: "rotate(360deg) translateX(50px) rotate(-360deg)" },
        },
        "neon-glow": {
          "0%, 100%": { filter: "brightness(1) drop-shadow(0 0 10px hsl(var(--neon-cyan)))" },
          "50%": { filter: "brightness(1.2) drop-shadow(0 0 20px hsl(var(--neon-cyan)))" },
        },
      },
      animation: {
        "accordion-down": "accordion-down 0.2s ease-out",
        "accordion-up": "accordion-up 0.2s ease-out",
        'sphere-float': 'sphere-float 6s ease-in-out infinite',
        'sphere-pulse': 'sphere-pulse 2s ease-in-out infinite',
        'particle-orbit': 'particle-orbit 4s linear infinite',
        'neon-glow': 'neon-glow 3s ease-in-out infinite',
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
} satisfies Config;
