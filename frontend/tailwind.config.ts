import type { Config } from 'tailwindcss'

const config: Config = {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        background: '#131313',
        surface: {
          DEFAULT: '#131313',
          dim: '#131313',
          lowest: '#0E0E0E',
          low: '#1B1B1B',
          container: '#1F1F1F',
          high: '#2A2A2A',
          highest: '#353535',
          bright: '#393939',
          variant: '#353535',
        },
        'on-surface': {
          DEFAULT: '#E2E2E2',
          variant: '#CFC2D6',
        },
        muted: '#666666',
        accent: {
          purple: '#A855F7',
          teal: '#1D9E75',
          green: '#639922',
        },
        primary: {
          DEFAULT: '#DDB7FF',
          container: '#B76DFF',
          fixed: '#F0DBFF',
          'fixed-dim': '#DDB7FF',
        },
        outline: {
          DEFAULT: '#988D9F',
          variant: '#4D4354',
        },
        'matte-silver': '#222222',
        brand: {
          purple: '#A855F7',
          border: '#222222',
          muted: '#666666',
          black: '#000000',
        },
        error: {
          DEFAULT: '#FFB4AB',
          container: '#93000A',
        },
        semantic: {
          red: '#FF4444',
          amber: '#FFAA00',
          green: '#44BB66',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['Space Grotesk', 'monospace'],
        headline: ['Inter', 'sans-serif'],
        body: ['Inter', 'sans-serif'],
        label: ['Space Grotesk', 'monospace'],
      },
      borderRadius: {
        none: '0px',
      },
      spacing: {
        '1': '4px',
        '2': '8px',
        '3': '12px',
        '4': '16px',
        '5': '20px',
        '6': '24px',
        '8': '32px',
        '10': '40px',
        '12': '48px',
        '16': '64px',
      },
    },
  },
  plugins: [],
}

export default config
