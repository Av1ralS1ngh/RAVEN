import axios from 'axios'
import { API_BASE_URL } from '@/constants'
import type {
  DiscoveryAnalyzeRequest,
  DiscoveryAnalyzeResponse,
  TrendingSkillsResponse,
} from '@/types/discovery.types'

const client = axios.create({ baseURL: API_BASE_URL })

function extractError(err: unknown): string {
  if (axios.isAxiosError(err)) {
    return err.response?.data?.error ?? err.response?.data?.detail ?? err.message
  }
  return String(err)
}

export async function analyzeDiscovery(
  payload: DiscoveryAnalyzeRequest,
): Promise<DiscoveryAnalyzeResponse> {
  try {
    const { data } = await client.post<DiscoveryAnalyzeResponse>('/api/discovery/analyze', payload)
    return data
  } catch (err) {
    return { success: false, data: null, error: extractError(err) }
  }
}

export async function getTrendingSkills(limit = 8): Promise<TrendingSkillsResponse> {
  try {
    const { data } = await client.get<TrendingSkillsResponse>('/api/discovery/trending', {
      params: { limit },
    })
    return data
  } catch (err) {
    return { success: false, data: null, error: extractError(err) }
  }
}
