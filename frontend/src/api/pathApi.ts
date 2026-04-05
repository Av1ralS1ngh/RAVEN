import axios from 'axios'
import { API_BASE_URL } from '@/constants'
import type { PathRequest, PathResponse } from '@/types/path.types'

const client = axios.create({ baseURL: API_BASE_URL })

/**
 * POST /api/path/find — find shortest connection path between two LinkedIn profiles.
 */
export async function findPath(payload: PathRequest): Promise<PathResponse> {
  try {
    const { data } = await client.post<PathResponse>('/api/path/find', payload)
    return data
  } catch (err) {
    if (axios.isAxiosError(err)) {
      const message: string =
        err.response?.data?.error ?? err.response?.data?.detail ?? err.message
      return { success: false, data: null, error: message }
    }
    return { success: false, data: null, error: String(err) }
  }
}
