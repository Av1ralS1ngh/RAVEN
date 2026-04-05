import { Component } from 'react'
import type { ErrorInfo, ReactNode } from 'react'
import Card from '@/components/ui/Card'
import Button from '@/components/ui/Button'
import { AlertTriangle } from 'lucide-react'

interface Props {
  children: ReactNode
}

interface State {
  hasError: boolean
  error: Error | null
}

export default class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo)
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-[#131313] flex items-center justify-center p-6 bg-surface">
          <Card className="max-w-md w-full flex flex-col items-center text-center p-8">
            <div className="w-12 h-12 rounded-none bg-[#93000A]/20 flex items-center justify-center mb-4 border border-[#FF4444]/30">
              <AlertTriangle className="text-[#FFB4AB] w-6 h-6" />
            </div>
            <h2 className="text-sm font-mono font-medium text-[#E2E2E2] mb-2 uppercase tracking-wide">
              Something went wrong
            </h2>
            <p className="text-xs text-[#CFC2D6] font-mono mb-6 bg-white/5 p-3 w-full overflow-auto">
              {this.state.error?.message ?? 'An unknown error occurred.'}
            </p>
            <Button
              variant="secondary"
              onClick={() => window.location.reload()}
              className="w-full justify-center"
            >
              Reload Page
            </Button>
          </Card>
        </div>
      )
    }

    return this.props.children
  }
}
