import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import axios from 'axios'
import 'bootstrap/dist/css/bootstrap.min.css'
import 'bootstrap/dist/js/bootstrap.bundle.min.js'

// Configure axios defaults
axios.defaults.baseURL = 'http://localhost:5000'
axios.defaults.withCredentials = true

// Add response interceptor for handling auth errors
axios.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 401) {
      // Redirect to login on auth error
      router.push('/login')
    }
    return Promise.reject(error)
  }
)

const app = createApp(App)
app.config.globalProperties.$http = axios
app.use(router)
app.mount('#app')
