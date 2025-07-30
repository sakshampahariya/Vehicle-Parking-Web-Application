<template>
  <div class="min-vh-100 d-flex align-items-center bg-light">
    <div class="container">
      <div class="row justify-content-center">
        <div class="col-md-6 col-lg-4">
          <div class="card shadow">
            <div class="card-body p-4">
              <div class="text-center mb-4">
                <h2 class="fw-bold">UrbanPark</h2>
                <p class="text-muted">Sign in to your account</p>
              </div>

              <form @submit.prevent="login">
                <div class="mb-3">
                  <label for="email" class="form-label">Email</label>
                  <input
                    type="email"
                    class="form-control"
                    id="email"
                    v-model="form.email"
                    required
                  >
                </div>

                <div class="mb-3">
                  <label for="password" class="form-label">Password</label>
                  <input
                    type="password"
                    class="form-control"
                    id="password"
                    v-model="form.password"
                    required
                  >
                </div>

                <div class="d-grid">
                  <button type="submit" class="btn btn-primary" :disabled="loading">
                    <span v-if="loading" class="spinner-border spinner-border-sm me-2"></span>
                    {{ loading ? 'Signing in...' : 'Sign In' }}
                  </button>
                </div>
              </form>

              <div class="text-center mt-4">
                <p class="mb-0">Don't have an account?</p>
                <router-link to="/register" class="text-decoration-none">Create one here</router-link>
              </div>

              
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'Login',
  data() {
    return {
      form: {
        email: '',
        password: ''
      },
      loading: false
    }
  },
  methods: {
    async login() {
      this.loading = true
      try {
        const response = await axios.post('/api/login', this.form)
        const user = response.data.user
        
        if (user.is_admin) {
          this.$router.push('/admin')
        } else {
          this.$router.push('/dashboard')
        }
      } catch (error) {
        alert(error.response?.data?.error || 'Login failed')
      } finally {
        this.loading = false
      }
    }
  }
}
</script>
