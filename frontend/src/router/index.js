import { createRouter, createWebHistory } from 'vue-router'
import Home from '@/views/Home.vue'
import Login from '@/views/Login.vue'
import Register from '@/views/Register.vue'
import AdminDashboard from '@/views/AdminDashboard.vue'
import UserDashboard from '@/views/UserDashboard.vue'
import ParkingLots from '@/views/ParkingLots.vue'
import MyReservations from '@/views/MyReservations.vue'
import axios from 'axios'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: Home
  },
  {
    path: '/login',
    name: 'Login',
    component: Login
  },
  {
    path: '/register',
    name: 'Register',
    component: Register
  },
  {
    path: '/admin',
    name: 'AdminDashboard',
    component: AdminDashboard,
    meta: { requiresAuth: true, requiresAdmin: true }
  },
  {
    path: '/dashboard',
    name: 'UserDashboard',
    component: UserDashboard,
    meta: { requiresAuth: true }
  },
  {
    path: '/parking-lots',
    name: 'ParkingLots',
    component: ParkingLots,
    meta: { requiresAuth: true }
  },
  {
    path: '/my-reservations',
    name: 'MyReservations',
    component: MyReservations,
    meta: { requiresAuth: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// Navigation guard
// In router/index.js - Check this section
router.beforeEach(async (to, from, next) => {
  if (to.matched.some(record => record.meta.requiresAuth)) {
    try {
      const response = await axios.get('/api/me')
      const user = response.data.user
      
      if (to.meta.requiresAdmin && !user.is_admin) {
        next('/dashboard')  // Make sure this redirects correctly
        return
      }
      
      next()
    } catch (error) {
      next('/login')
    }
  } else {
    next()
  }
})

export default router
