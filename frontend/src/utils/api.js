import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 10000
})

api.interceptors.response.use(
  response => response.data,
  error => {
    console.error('API Error:', error)
    return Promise.reject(error)
  }
)

export default {
  getAlerts(params) {
    return api.get('/alerts', { params })
  },
  getAlert(id) {
    return api.get(`/alerts/${id}`)
  },
  getDashboardStats() {
    return api.get('/stats/dashboard')
  },
  getTrend(params) {
    return api.get('/stats/trend', { params })
  },
  getAttackTypes(params) {
    return api.get('/stats/attack-types', { params })
  },
  getTopIPs(params) {
    return api.get('/stats/top-ips', { params })
  }
}
