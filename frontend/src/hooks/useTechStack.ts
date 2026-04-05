import { useState, useCallback } from 'react'
import { analyzeStack, getBlastDetail } from '@/api/blastApi'
import type { AnalyzeResult, FileImpactEntry } from '@/types/blast.types'

interface UseTechStackState {
  recruiterUrl: string
  githubUsername: string
  isLoading: boolean
  error: string | null
  result: AnalyzeResult | null
  selectedLib: string | null
  blastDetail: FileImpactEntry[] | null
  isLoadingDetail: boolean
}

interface UseTechStackReturn extends UseTechStackState {
  setRecruiterUrl: (v: string) => void
  setGithubUsername: (v: string) => void
  submit: () => Promise<void>
  selectLib: (libName: string) => Promise<void>
  reset: () => void
}

const INITIAL: UseTechStackState = {
  recruiterUrl: '',
  githubUsername: '',
  isLoading: false,
  error: null,
  result: null,
  selectedLib: null,
  blastDetail: null,
  isLoadingDetail: false,
}

export function useTechStack(): UseTechStackReturn {
  const [state, setState] = useState<UseTechStackState>(INITIAL)

  const setRecruiterUrl = useCallback((v: string) => {
    setState(s => ({ ...s, recruiterUrl: v, error: null }))
  }, [])

  const setGithubUsername = useCallback((v: string) => {
    setState(s => ({ ...s, githubUsername: v, error: null }))
  }, [])

  const submit = useCallback(async () => {
    const { recruiterUrl, githubUsername } = state

    if (!recruiterUrl.trim()) {
      setState(s => ({ ...s, error: 'Please enter the recruiter LinkedIn URL.' }))
      return
    }
    if (!githubUsername.trim()) {
      setState(s => ({ ...s, error: 'Please enter your GitHub username.' }))
      return
    }

    setState(s => ({ ...s, isLoading: true, error: null, result: null, selectedLib: null, blastDetail: null }))

    const response = await analyzeStack({
      recruiter_url: recruiterUrl.trim(),
      github_username: githubUsername.trim(),
    })

    if (response.success && response.data) {
      setState(s => ({
        ...s,
        isLoading: false,
        result: response.data,
        error: null,
      }))
    } else {
      setState(s => ({
        ...s,
        isLoading: false,
        error: typeof response.error === 'string'
          ? response.error
          : JSON.stringify(response.error) ?? 'An unknown error occurred.',
      }))
    }
  }, [state])

  const selectLib = useCallback(async (libName: string) => {
    setState(s => ({ ...s, selectedLib: libName, blastDetail: null, isLoadingDetail: true }))

    const response = await getBlastDetail(libName)

    setState(s => ({
      ...s,
      isLoadingDetail: false,
      blastDetail: response.success && response.data ? response.data : [],
    }))
  }, [])

  const reset = useCallback(() => {
    setState(INITIAL)
  }, [])

  return {
    ...state,
    setRecruiterUrl,
    setGithubUsername,
    submit,
    selectLib,
    reset,
  }
}
