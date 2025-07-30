<template>
  <div class="min-vh-100 d-flex align-items-center bg-light">
    <div class="container">
      <div class="row justify-content-center">
        <div class="col-md-8 col-lg-6">
          <div class="card shadow">
            <div class="card-body p-4">
              <div class="text-center mb-4">
                <h2 class="fw-bold">UrbanPark</h2>
                <p class="text-muted">Create your account</p>
              </div>

              <form @submit.prevent="register">
                <div class="row">
                  <div class="col-md-6">
                    <div class="mb-3">
                      <label for="full_name" class="form-label">Full Name *</label>
                      <input
                        type="text"
                        class="form-control"
                        id="full_name"
                        v-model="form.full_name"
                        required
                      >
                    </div>
                  </div>
                  <div class="col-md-6">
                    <div class="mb-3">
                      <label for="email" class="form-label">Email *</label>
                      <input
                        type="email"
                        class="form-control"
                        id="email"
                        v-model="form.email"
                        required
                      >
                    </div>
                  </div>
                </div>

                <div class="row">
                  <div class="col-md-6">
                    <div class="mb-3">
                      <label for="phone" class="form-label">Phone Number *</label>
                      <input
                        type="tel"
                        class="form-control"
                        id="phone"
                        v-model="form.phone"
                        required
                      >
                    </div>
                  </div>
                  <div class="col-md-6">
                    <div class="mb-3">
                      <label for="pin_code" class="form-label">PIN Code *</label>
                      <input
                        type="text"
                        class="form-control"
                        id="pin_code"
                        v-model="form.pin_code"
                        required
                      >
                    </div>
                  </div>
                </div>

                <div class="mb-3">
                  <label for="address" class="form-label">Address *</label>
                  <textarea
                    class="form-control"
                    id="address"
                    rows="2"
                    v-model="form.address"
                    required
                  ></textarea>
                </div>

                <div class="mb-3">
                  <label for="password" class="form-label">Password *</label>
                  <input
                    type="password"
                    class="form-control"
                    id="password"
                    v-model="form.password"
                    required
                    minlength="6"
                  >
                </div>

                <div class="d-grid">
                  <button type="submit" class="btn btn-primary" :disabled="loading">
                    <span v-if="loading" class="spinner-border spinner-border-sm me-2"></span>
                    {{ loading ? 'Creating Account...' : 'Create Account' }}
                  </button>
                </div>
              </form>

              <div class="text-center mt-4">
                <p class="mb-0">Already have an account?</p>
                <router-link to="/login" class="text-decoration-none">Sign in here</router-link>
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
  name: 'Register',
  data() {
    return {
      form: {
        full_name: '',
        email: '',
        phone: '',
        address: '',
        pin_code: '',
        password: ''
      },
      loading: false
    }
  },
  methods: {
    async register() {
      this.loading = true
      try {
        await axios.post('/api/register', this.form)
        alert('Registration successful! Please login.')
        this.$router.push('/login')
      } catch (error) {
        alert(error.response?.data?.error || 'Registration failed')
      } finally {
        this.loading = false
      }
    }
  }
}
</script>
