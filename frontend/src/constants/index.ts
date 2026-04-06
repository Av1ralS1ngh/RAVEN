export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

export const ROUTES = {
  LANDING: '/',
  PATH_FINDER: '/dashboard',
  TECH_STACK: '/tech-stack',
  WHAT_TO_CHOOSE: '/discovery',
} as const

export const COLORS = {
  background: '#131313',
  surface: {
    default: '#131313',
    lowest: '#0E0E0E',
    low: '#1B1B1B',
    container: '#1F1F1F',
    high: '#2A2A2A',
    highest: '#353535',
    bright: '#393939',
  },
  text: {
    primary: '#E2E2E2',
    secondary: '#CFC2D6',
    muted: '#666666',
  },
  accent: {
    purple: '#A855F7',
    teal: '#1D9E75',
    green: '#639922',
  },
  primary: {
    default: '#DDB7FF',
    container: '#B76DFF',
  },
  outline: {
    default: '#988D9F',
    variant: '#4D4354',
  },
  matteSilver: '#222222',
  semantic: {
    red: '#FF4444',
    amber: '#FFAA00',
    green: '#44BB66',
  },
} as const
