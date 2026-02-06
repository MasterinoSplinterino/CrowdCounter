// All API requests go through Next.js API proxy (same domain)
// Browser: crown.nemytnaya.ru/api/... → Next.js → backend:8000/api/...
// No external API exposure - backend only accessible inside Docker network

export interface ApiRoom {
  id: string
  name: string
  capacity: number
  camera_url: string
  is_active: boolean
  created_at: string
  count: number
  raw_count: number
  occupancy_percent: number
  status: 'empty' | 'low' | 'medium' | 'high' | 'full'
  last_updated: string | null
}

export interface ApiSettings {
  model: string
  confidence_threshold: number
  detection_interval: number
  smoothing_alpha: number
  imgsz: number
}

export interface ApiStatus {
  device: string
  model: string
  model_loaded: boolean
  cameras_connected: number
  cameras_total: number
  uptime_seconds: number
  avg_inference_ms: number
}

export interface ApiModel {
  id: string
  name: string
  description: string
  type: 'person' | 'head'
}

export interface ApiCount {
  id: number
  room_id: string
  count: number
  raw_count: number
  occupancy: number
  timestamp: string
}

export interface CreateRoomData {
  id: string
  name: string
  capacity: number
  camera_url: string
  is_active?: boolean
}

export interface UpdateRoomData {
  name?: string
  capacity?: number
  camera_url?: string
  is_active?: boolean
}

async function request<T>(endpoint: string, options?: RequestInit): Promise<T> {
  // Requests to /api/... are proxied by Next.js to backend
  const res = await fetch(endpoint, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  })

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: 'Unknown error' }))
    throw new Error(error.detail || error.error || `HTTP ${res.status}`)
  }

  if (res.status === 204) {
    return null as T
  }

  return res.json()
}

export const api = {
  // Rooms
  getRooms: () => request<ApiRoom[]>('/api/rooms'),
  getRoom: (id: string) => request<ApiRoom>(`/api/rooms/${id}`),
  createRoom: (data: CreateRoomData) =>
    request<ApiRoom>('/api/rooms', { method: 'POST', body: JSON.stringify(data) }),
  updateRoom: (id: string, data: UpdateRoomData) =>
    request<ApiRoom>(`/api/rooms/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteRoom: (id: string) =>
    request<void>(`/api/rooms/${id}`, { method: 'DELETE' }),

  // Counts
  getCurrentCount: (roomId: string) =>
    request<{ count: number; raw_count: number; occupancy_percent: number; status: string }>(`/api/rooms/${roomId}/current`),
  getHistory: (roomId: string, hours: number = 10) =>
    request<ApiCount[]>(`/api/rooms/${roomId}/history?hours=${hours}`),

  // Preview
  getPreview: (roomId: string) =>
    request<{ room_id: string; frame: string; detections: number; timestamp: string }>(`/api/rooms/${roomId}/preview`),

  // Settings
  getSettings: () => request<ApiSettings>('/api/settings'),
  updateSettings: (data: Partial<ApiSettings>) =>
    request<ApiSettings>('/api/settings', { method: 'PUT', body: JSON.stringify(data) }),

  // Models
  getModels: () => request<ApiModel[]>('/api/models'),

  // Status
  getStatus: () => request<ApiStatus>('/api/status'),
}
