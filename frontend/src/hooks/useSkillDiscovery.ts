import { useCallback, useState } from 'react'
import { analyzeDiscovery, getTrendingSkills } from '@/api/discoveryApi'
import type {
  DiscoveryAnalyzeResult,
  SkillQuizAnswers,
  TrendingSkillItem,
} from '@/types/discovery.types'

interface UseSkillDiscoveryState {
  isLoading: boolean
  isLoadingTrending: boolean
  error: string | null
  result: DiscoveryAnalyzeResult | null
  warning: string | null
  trending: TrendingSkillItem[]
}

interface UseSkillDiscoveryReturn extends UseSkillDiscoveryState {
  submitQuiz: (answers: SkillQuizAnswers) => Promise<void>
  loadTrending: (limit?: number) => Promise<void>
  reset: () => void
}

const INITIAL: UseSkillDiscoveryState = {
  isLoading: false,
  isLoadingTrending: false,
  error: null,
  result: null,
  warning: null,
  trending: [],
}

export function useSkillDiscovery(): UseSkillDiscoveryReturn {
  const [state, setState] = useState<UseSkillDiscoveryState>(INITIAL)

  const submitQuiz = useCallback(async (answers: SkillQuizAnswers) => {
    setState(s => ({ ...s, isLoading: true, error: null, warning: null }))

    const response = await analyzeDiscovery({
      answers,
      related_limit: 14,
      resource_limit: 8,
    })

    if (response.success && response.data) {
      setState(s => ({
        ...s,
        isLoading: false,
        result: response.data,
        warning: response.error,
        error: null,
      }))
      return
    }

    setState(s => ({
      ...s,
      isLoading: false,
      error:
        typeof response.error === 'string'
          ? response.error
          : JSON.stringify(response.error) ?? 'Discovery analysis failed.',
    }))
  }, [])

  const loadTrending = useCallback(async (limit = 8) => {
    setState(s => ({ ...s, isLoadingTrending: true }))

    const response = await getTrendingSkills(limit)

    if (response.success && response.data) {
      setState(s => ({
        ...s,
        isLoadingTrending: false,
        trending: response.data?.skills ?? [],
      }))
      return
    }

    // Trending data is non-blocking; preserve existing fallback UI.
    setState(s => ({
      ...s,
      isLoadingTrending: false,
      warning:
        typeof response.error === 'string'
          ? response.error
          : s.warning,
    }))
  }, [])

  const reset = useCallback(() => {
    setState(s => ({ ...s, result: null, error: null, warning: null }))
  }, [])

  return {
    ...state,
    submitQuiz,
    loadTrending,
    reset,
  }
}
