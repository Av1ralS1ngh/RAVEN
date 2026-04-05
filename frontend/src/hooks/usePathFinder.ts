import { useState, useCallback } from 'react'
import { findPath } from '@/api/pathApi'
import type { PathResult } from '@/types/path.types'

interface UsePathFinderState {
  recruiterUrl: string
  yourLinkedInId: string
  isLoading: boolean
  error: string | null
  result: PathResult | null
}

interface UsePathFinderReturn extends UsePathFinderState {
  setRecruiterUrl: (v: string) => void
  setYourLinkedInId: (v: string) => void
  submit: () => Promise<void>
  reset: () => void
}

const INITIAL: UsePathFinderState = {
  recruiterUrl: '',
  yourLinkedInId: '',
  isLoading: false,
  error: null,
  result: null,
}

/**
 * Encapsulates all state and async logic for the Module 1 path-finder flow.
 *
 * Usage:
 *   const { recruiterUrl, setRecruiterUrl, submit, result, isLoading, error } = usePathFinder()
 */
export function usePathFinder(): UsePathFinderReturn {
  const [state, setState] = useState<UsePathFinderState>(INITIAL)

  const setRecruiterUrl = useCallback((v: string) => {
    setState(s => ({ ...s, recruiterUrl: v, error: null }))
  }, [])

  const setYourLinkedInId = useCallback((v: string) => {
    setState(s => ({ ...s, yourLinkedInId: v, error: null }))
  }, [])

  const submit = useCallback(async () => {
    const { recruiterUrl, yourLinkedInId } = state

    if (!recruiterUrl.trim()) {
      setState(s => ({ ...s, error: 'Please enter the recruiter LinkedIn URL.' }))
      return
    }
    if (!yourLinkedInId.trim()) {
      setState(s => ({ ...s, error: 'Please enter your LinkedIn username.' }))
      return
    }

    setState(s => ({ ...s, isLoading: true, error: null }))

    const response = await findPath({
      recruiter_url: recruiterUrl.trim(),
      your_linkedin_id: yourLinkedInId.trim().replace(/^.*\/in\//i, '').replace(/\/$/, ''),
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
        error: response.error ? (typeof response.error === 'string' ? response.error : JSON.stringify(response.error)) : 'An unknown error occurred.',
      }))
    }
  }, [state])

  const reset = useCallback(() => {
    setState(s => ({ ...s, result: null, error: null }))
  }, [])

  return {
    ...state,
    setRecruiterUrl,
    setYourLinkedInId,
    submit,
    reset,
  }
}
