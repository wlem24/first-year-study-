import axios from 'axios'

const getBaseURL = () => {
  const envUrl = import.meta.env.VITE_API_BASE_URL || import.meta.env.VITE_API_URL
  if (envUrl && envUrl.trim()) {
    const trimmed = envUrl.trim().replace(/\/+$/, '')
    return trimmed.endsWith('/api/v1') ? trimmed : `${trimmed}/api/v1`
  }
  return '/api/v1'
}

const api = axios.create({
  baseURL: getBaseURL(),
  withCredentials: true,
  headers: { 'Content-Type': 'application/json' },
})

// ── Request Interceptor: Attach Bearer token for cross-domain auth ──

api.interceptors.request.use((config) => {
  try {
    const token = localStorage.getItem('access_token')
    if (token && !config.headers.Authorization) {
      config.headers.Authorization = `Bearer ${token}`
    }
    const refreshToken = localStorage.getItem('refresh_token')
    if (refreshToken && !config.headers['X-Refresh-Token']) {
      config.headers['X-Refresh-Token'] = refreshToken
    }
  } catch {
    // Ignore localStorage access restrictions if any
  }
  return config
})

// ── Response Interceptor: Safe Auto-Refresh on 401 ───────────

let isRefreshing = false
let failedQueue = []

const processQueue = (error) => {
  failedQueue.forEach(({ resolve, reject }) => {
    error ? reject(error) : resolve()
  })
  failedQueue = []
}

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config
    const isAuthEndpoint = originalRequest?.url?.includes('/auth/')

    // Avoid refresh loops for auth endpoints
    if (error.response?.status === 401 && !originalRequest?._retry && !isAuthEndpoint) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject })
        }).then(() => api(originalRequest))
      }

      originalRequest._retry = true
      isRefreshing = true

      try {
        const refreshRes = await api.post('/auth/refresh')
        if (refreshRes.data?.access_token) {
          try {
            localStorage.setItem('access_token', refreshRes.data.access_token)
          } catch {}
        }
        processQueue(null)
        return api(originalRequest)
      } catch (refreshError) {
        processQueue(refreshError)
        try {
          localStorage.removeItem('access_token')
          localStorage.removeItem('refresh_token')
        } catch {}
        window.location.href = '/login'
        return Promise.reject(refreshError)
      } finally {
        isRefreshing = false
      }
    }

    return Promise.reject(error)
  }
)

// ── Auth Endpoints ─────────────────────────────────────────────

export async function login(email, password) {
  const res = await api.post('/auth/login', { email, password })
  if (res.data?.access_token) {
    try {
      localStorage.setItem('access_token', res.data.access_token)
      if (res.data?.refresh_token) {
        localStorage.setItem('refresh_token', res.data.refresh_token)
      }
    } catch {}
  }
  return res.data
}

export async function logout() {
  try {
    await api.post('/auth/logout')
  } finally {
    try {
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
    } catch {}
  }
}

export async function checkAuth() {
  const res = await api.get('/auth/me')
  return res.data
}

// ── School Board Posts Endpoints ───────────────────────────────

export async function getPosts({ category, search, page = 1, pageSize = 12 } = {}) {
  const params = { page, page_size: pageSize }
  if (category && category !== 'all') params.category = category
  if (search) params.search = search

  const res = await api.get('/posts/', { params })
  return res.data
}

export async function getPost(id) {
  const res = await api.get(`/posts/${id}`)
  return res.data
}

export async function createPost(formData) {
  const res = await api.post('/posts/', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return res.data
}

export async function updatePost(id, formData) {
  const res = await api.put(`/posts/${id}`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return res.data
}

export async function deletePost(id) {
  const res = await api.delete(`/posts/${id}`)
  return res.data
}

export async function syncPadlet(id) {
  const res = await api.post(`/posts/${id}/sync-padlet`)
  return res.data
}

export async function likePost(id) {
  const res = await api.post(`/posts/${id}/like`)
  return res.data
}

export async function updateProfile(data) {
  const res = await api.put('/auth/me', data)
  return res.data
}

export default api
