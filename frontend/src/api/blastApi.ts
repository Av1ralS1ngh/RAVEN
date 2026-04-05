import axios from 'axios'
import { API_BASE_URL } from '@/constants'
import type { AnalyzeResponse, BlastDetailResponse } from '@/types/blast.types'

const client = axios.create({ baseURL: API_BASE_URL })

function extractError(err: unknown): string {
  if (axios.isAxiosError(err)) {
    return err.response?.data?.error ?? err.response?.data?.detail ?? err.message
  }
  return String(err)
}

/**
 * POST /api/blast/analyze
 * Scrapes a recruiter LinkedIn profile and parses a GitHub user's repos,
 * then returns tech stack + dependency blast radius.
 */
export async function analyzeStack(payload: {
  recruiter_url: string
  github_username: string
}): Promise<AnalyzeResponse> {
  try {
    const { data } = await client.post<AnalyzeResponse>('/api/blast/analyze', payload)
    return data
  } catch (err) {
    return { success: false, data: null, error: extractError(err) }
  }
}

/**
 * POST /api/blast/blast-detail
 * Fetches per-file impact detail for a single library.
 */
export async function getBlastDetail(lib_name: string): Promise<BlastDetailResponse> {
  try {
    const { data } = await client.post<BlastDetailResponse>('/api/blast/blast-detail', {
      lib_name,
    })
    return data
  } catch (err) {
    return { success: false, data: null, error: extractError(err) }
  }
}
