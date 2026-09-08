import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || import.meta.env.VITE_API_URL || '/api/v1',
  withCredentials: true,
  headers: { 'Content-Type': 'application/json' },
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
        await api.post('/auth/refresh')
        processQueue(null)
        return api(originalRequest)
      } catch (refreshError) {
        processQueue(refreshError)
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
  return res.data
}

export async function logout() {
  await api.post('/auth/logout')
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
