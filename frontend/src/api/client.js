import axios from 'axios'

const api = axios.create({ baseURL: '/api', timeout: 30000 })

api.interceptors.request.use(config => {
  window.dispatchEvent(new CustomEvent('api:loading', { detail: true }))
  return config
})

api.interceptors.response.use(
  res => {
    window.dispatchEvent(new CustomEvent('api:loading', { detail: false }))
    return res
  },
  err => {
    window.dispatchEvent(new CustomEvent('api:loading', { detail: false }))
    const msg = err.response?.data?.detail || err.message || 'Network error'
    window.dispatchEvent(new CustomEvent('api:error', { detail: msg }))
    return Promise.reject(err)
  }
)

export default api
