export interface User {
  id: number
  username: string
  email: string
  first_name?: string
  last_name?: string
}

export interface UserProfile {
  id?: number
  user?: User
  has_api_key?: boolean
  daily_usage?: number
  total_input_tokens?: number
  total_output_tokens?: number
}

export interface Subject {
  id: number
  name: string
  code?: string
  description?: string
  units?: Unit[]
  progress?: number
}

export interface Unit {
  id: number
  name: string
  order?: number
  topics?: Topic[]
}

export interface Topic {
  id: number
  name: string
  order?: number
  unit?: number
  is_completed?: boolean
}

export interface Note {
  id: number
  topic: number
  content: string
}

export interface MindmapNode {
  id: string
  label: string
  [key: string]: unknown
}

export interface Mindmap {
  id?: number
  topic?: number
  title?: string
  nodes?: MindmapNode[]
  edges?: unknown[]
  [key: string]: unknown
}

export interface Flashcard {
  id: number
  topic: number
  front: string
  back: string
  interval?: number
  repetition?: number
  ease_factor?: number
}

export interface MCQOption {
  id?: number
  text: string
  is_correct?: boolean
}

export interface MCQ {
  id: number
  topic: number
  question: string
  options: string[] | MCQOption[]
  explanation?: string
}

const BASE_URL = '/api'

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const token = localStorage.getItem('token')
  const neonToken = localStorage.getItem('neon_access_token')

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
  }

  if (neonToken) {
    headers['Authorization'] = `Bearer ${neonToken}`
  } else if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  const response = await fetch(`${BASE_URL}${endpoint}`, {
    ...options,
    headers,
  })

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}))
    throw new Error(errorData.detail || errorData.error || 'API Request Failed')
  }

  return response.json()
}

export const api = {
  get: <T>(endpoint: string) => request<T>(endpoint, { method: 'GET' }),
  post: <T>(endpoint: string, body?: unknown) =>
    request<T>(endpoint, {
      method: 'POST',
      body: body ? JSON.stringify(body) : undefined,
    }),
  put: <T>(endpoint: string, body?: unknown) =>
    request<T>(endpoint, {
      method: 'PUT',
      body: body ? JSON.stringify(body) : undefined,
    }),
  patch: <T>(endpoint: string, body?: unknown) =>
    request<T>(endpoint, {
      method: 'PATCH',
      body: body ? JSON.stringify(body) : undefined,
    }),
  delete: <T>(endpoint: string) => request<T>(endpoint, { method: 'DELETE' }),
}
