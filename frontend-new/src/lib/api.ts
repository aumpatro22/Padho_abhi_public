export interface User {
  id: number
  username: string
  email: string
}

export interface UserProfile {
  id: number
  daily_usage: number
  has_api_key: boolean
}

export interface Topic {
  id: number
  unit: number
  name: string
  order: number
  has_notes?: boolean
  created_at?: string
}

export interface Unit {
  id: number
  subject: number
  unit_number: number
  title: string
  topics?: Topic[]
}

export interface Subject {
  id: number
  name: string
  user: number
  created_at?: string
  units?: Unit[]
}

export interface Note {
  id: number
  topic: number
  content: string
}

export interface Mindmap {
  id: number
  topic: number
  data: unknown
}

export interface Flashcard {
  id: number
  topic: number
  front: string
  back: string
}

export interface MCQ {
  id: number
  topic: number
  question: string
  options: string[]
  answer: number
}

export const api = {
  get: async <T = unknown>(url: string): Promise<T> => {
    const res = await fetch(`/api${url}`)
    return res.json()
  },
  post: async <T = unknown>(url: string, body?: unknown): Promise<T> => {
    const res = await fetch(`/api${url}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    })
    return res.json()
  },
  delete: async <T = unknown>(url: string): Promise<T> => {
    const res = await fetch(`/api${url}`, { method: "DELETE" })
    return res.json()
  },
}
