<template>
  <div>
    <!-- Navigation -->
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
      <div class="container">
        <router-link class="navbar-brand fw-bold" to="/dashboard">
        UrbanPark
        </router-link>
        <div class="d-flex align-items-center gap-3">
          <router-link class="btn btn-link text-light text-decoration-none" to="/parking-lots">
            Find Parking
          </router-link>
          <button class="btn btn-link text-light text-decoration-none" @click="showSummaryModal">
            Summary
          </button>
          <router-link class="btn btn-link text-light text-decoration-none" to="/my-reservations">
            My Bookings
          </router-link>          
          <button class="btn btn-outline-light btn-sm" @click="logout">
            Logout
          </button>
        </div>
      </div>
    </nav>

    <div class="container py-4">
      <h2 class="mb-4">My Parking Reservations</h2>
      
      <!-- Active Reservations -->
      <div v-if="activeReservations.length > 0" class="mb-5">
        <h4 class="text-primary mb-3">🚗 Active Bookings</h4>
        <div class="row">
          <div class="col-lg-6 mb-3" v-for="reservation in activeReservations" :key="reservation.id">
            <div class="card border-primary">
              <div class="card-header bg-primary text-white d-flex justify-content-between align-items-center">
                <h6 class="mb-0">{{ reservation.lot_name }}</h6>
                <span class="badge bg-light text-primary">Spot ID: {{ reservation.spot_id }}</span>
              </div>
              <div class="card-body">
                <p class="mb-1"><strong>Location:</strong> {{ reservation.lot_address }}</p>
                <p class="mb-1"><strong>Vehicle:</strong> {{ reservation.vehicle_number }}</p>
                <p class="mb-1"><strong>Parked Since:</strong> {{ formatDateTime(reservation.parking_timestamp) }}</p>
                <p class="mb-1"><strong>Duration:</strong> {{ calculateLiveDuration(reservation.parking_timestamp) }}</p>
                <p class="mb-3"><strong>Current Cost:</strong> ₹{{ calculateLiveCost(reservation) }}</p>
                
                <button class="btn btn-warning w-100" @click="showReleaseModal(reservation)">
                  <i class="fas fa-sign-out-alt me-1"></i>Release Parking
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- No Active Reservations -->
      <div v-if="activeReservations.length === 0" class="text-center py-4 mb-5">
        <i class="fas fa-car fa-3x text-muted mb-3"></i>
        <p class="text-muted">No active parking bookings.</p>
        <router-link to="/parking-lots" class="btn btn-primary">
          <i class="fas fa-search me-2"></i>Find Parking Spots
        </router-link>
      </div>
      
      <!-- Completed Reservations -->
      <div>
        <h4 class="text-success mb-3">📋 Booking History</h4>
        
        <div v-if="completedReservations.length === 0" class="text-center py-5">
          <i class="fas fa-history fa-3x text-muted mb-3"></i>
          <p class="text-muted">No completed bookings yet.</p>
        </div>
        
        <div v-else class="table-responsive">
          <table class="table table-hover">
            <thead class="table-light">
              <tr>
                <th>Spot ID</th>
                <th>Location</th>
                <th>Vehicle</th>
                <th>Parking Time</th>
                <th>Duration</th>
                <th>Cost</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="reservation in completedReservations" :key="reservation.id">
                <td><span class="badge bg-secondary">{{ reservation.spot_id }}</span></td>
                <td>
                  <strong>{{ reservation.lot_name }}</strong><br>
                  <small class="text-muted">{{ reservation.lot_address }}</small>
                </td>
                <td>{{ reservation.vehicle_number }}</td>
                <td>{{ formatDateTime(reservation.parking_timestamp) }}</td>
                <td>{{ reservation.duration_display || 'N/A' }}</td>
                <td class="fw-bold text-success">₹{{ (reservation.parking_cost || 0).toFixed(2) }}</td>
                <td><span class="badge bg-success">Completed</span></td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- Release Parking Modal -->
    <div class="modal fade" :class="{ show: showReleaseModalFlag }" :style="{ display: showReleaseModalFlag ? 'block' : 'none' }" tabindex="-1">
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header bg-warning">
            <h5 class="modal-title">🚗 Release Parking Spot</h5>
            <button type="button" class="btn-close" @click="closeReleaseModal"></button>
          </div>
          
          <div class="modal-body" v-if="releaseReservation">
            <h6>Booking Details</h6>
            <table class="table table-sm">
              <tbody>
                <tr>
                  <td><strong>Spot ID:</strong></td>
                  <td>{{ releaseReservation.spot_id }}</td>
                </tr>
                <tr>
                  <td><strong>Location:</strong></td>
                  <td>{{ releaseReservation.lot_name }}</td>
                </tr>
                <tr>
                  <td><strong>Vehicle Number:</strong></td>
                  <td>{{ releaseReservation.vehicle_number }}</td>
                </tr>
                <tr>
                  <td><strong>Parking Time:</strong></td>
                  <td>{{ formatDateTime(releaseReservation.parking_timestamp) }}</td>
                </tr>
                <tr>
                  <td><strong>Releasing Time:</strong></td>
                  <td>{{ formatDateTime(new Date().toISOString()) }}</td>
                </tr>
                <tr>
                  <td><strong>Duration:</strong></td>
                  <td>{{ calculateLiveDuration(releaseReservation.parking_timestamp) }}</td>
                </tr>
                <tr>
                  <td><strong>Total Cost:</strong></td>
                  <td class="fw-bold text-primary">₹{{ calculateLiveCost(releaseReservation) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
          
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" @click="closeReleaseModal">Cancel</button>
            <button type="button" class="btn btn-warning" @click="confirmRelease" :disabled="loading">
              <span v-if="loading" class="spinner-border spinner-border-sm me-2"></span>
              {{ loading ? 'Releasing...' : 'Confirm Release' }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Summary Modal -->
    <div
      class="modal fade"
      :class="{ show: showChartsModal }"
      :style="{ display: showChartsModal ? 'block' : 'none' }"
      tabindex="-1"
    >
      <div class="modal-dialog modal-xl">
        <div class="modal-content">
          <div class="modal-header bg-primary text-white">
            <h5 class="modal-title">
              <i class="fas fa-chart-bar me-2"></i>Summary Analytics
            </h5>
            <button type="button" class="btn-close btn-close-white" @click="closeChartsModal"></button>
          </div>

          <div class="modal-body">
            <!-- Stats Cards -->
            <div class="row mb-4">
              <div class="col-md-3">
                <div class="card bg-primary text-white">
                  <div class="card-body text-center">
                    <h3>{{ stats.total_bookings }}</h3>
                    <p class="mb-0">Total Bookings</p>
                  </div>
                </div>
              </div>
              
              <div class="col-md-3">
                <div class="card bg-success text-white">
                  <div class="card-body text-center">
                    <h3>{{ stats.completed_bookings }}</h3>
                    <p class="mb-0">Completed</p>
                  </div>
                </div>
              </div>
              
              <div class="col-md-3">
                <div class="card bg-warning text-white">
                  <div class="card-body text-center">
                    <h3>{{ stats.active_bookings }}</h3>
                    <p class="mb-0">Active Bookings</p>
                  </div>
                </div>
              </div>
              
              <div class="col-md-3">
                <div class="card bg-info text-white">
                  <div class="card-body text-center">
                    <h3>₹{{ stats.total_spent }}</h3>
                    <p class="mb-0">Total Spent</p>
                  </div>
                </div>
              </div>
            </div>

            <!-- Charts Row -->
            <div class="row">
              <div class="col-md-6">
                <div class="card">
                  <div class="card-header">
                    <h6 class="mb-0">📊 Daily Spending (Last 7 Days)</h6>
                  </div>
                  <div class="card-body">
                    <div style="position: relative; height: 300px;">
                      <canvas ref="dailySpendingChart"></canvas>
                    </div>
                  </div>
                </div>
              </div>
              
              <div class="col-md-6">
                <div class="card">
                  <div class="card-header">
                    <h6 class="mb-0">🅿️ Most Used Parking Lots</h6>
                  </div>
                  <div class="card-body">
                    <div style="position: relative; height: 300px;">
                      <canvas ref="parkingUsageChart"></canvas>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" @click="closeChartsModal">Close</button>
          </div>
        </div>
      </div>
    </div>

    <!-- Modal Backdrop -->
    <div v-if="showReleaseModalFlag || showChartsModal" class="modal-backdrop fade show"></div>
  </div>
</template>

<script>
import axios from 'axios'
import { Chart, registerables } from 'chart.js'

Chart.register(...registerables)

export default {
  name: 'MyReservations',
  data() {
    return {
      user: null,
      reservations: [],
      releaseReservation: null,
      showReleaseModalFlag: false,
      loading: false,
      // ADDED: Summary modal data
      showChartsModal: false,
      stats: {
        total_bookings: 0,
        active_bookings: 0,
        completed_bookings: 0,
        total_spent: 0
      }
    }
  },
  computed: {
    activeReservations() {
      return this.reservations.filter(r => r.status === 'active')
    },
    completedReservations() {
      return this.reservations.filter(r => r.status === 'completed').reverse()
    }
  },
  async mounted() {
    await this.loadUserInfo()
    await this.loadReservations()
    await this.loadStats()
  },
  methods: {
    async loadUserInfo() {
      try {
        const response = await axios.get('/api/me')
        this.user = response.data.user
      } catch (error) {
        console.error('User info error:', error)
        this.$router.push('/login')
      }
    },
    
    async loadReservations() {
      try {
        console.log('Loading reservations...')
        const response = await axios.get('/api/my-reservations')
        this.reservations = response.data
        console.log('✅ Loaded reservations:', this.reservations)
        console.log('Active reservations:', this.activeReservations)
      } catch (error) {
        console.error('❌ Error loading reservations:', error)
        console.error('Response:', error.response?.data)
      }
    },

    // ADDED: Load stats for summary modal
    async loadStats() {
      try {
        const response = await axios.get('/api/user-dashboard-stats')
        this.stats = response.data
      } catch (error) {
        console.error('Error loading stats:', error)
      }
    },

    // ADDED: Summary Modal Functions
    showSummaryModal() {
      this.showChartsModal = true
      this.$nextTick(() => {
        setTimeout(() => this.renderCharts(), 300)
      })
    },

    closeChartsModal() {
      this.showChartsModal = false
      // Clean up charts
      const dailyChart = Chart.getChart(this.$refs.dailySpendingChart)
      if (dailyChart) dailyChart.destroy()
      const usageChart = Chart.getChart(this.$refs.parkingUsageChart)
      if (usageChart) usageChart.destroy()
    },
    
    renderCharts() {
      this.renderDailySpendingChart()
      this.renderParkingUsageChart()
    },
    
    renderDailySpendingChart() {
      const completedReservations = this.reservations.filter(r => r.status === 'completed' && r.parking_cost)
      
      const dailySpending = {}
      completedReservations.forEach(reservation => {
        const date = new Date(reservation.parking_timestamp).toLocaleDateString('en-IN')
        dailySpending[date] = (dailySpending[date] || 0) + parseFloat(reservation.parking_cost || 0)
      })
      
      const last7Days = []
      const spending = []
      
      for (let i = 6; i >= 0; i--) {
        const date = new Date()
        date.setDate(date.getDate() - i)
        const dateStr = date.toLocaleDateString('en-IN')
        last7Days.push(dateStr)
        spending.push(dailySpending[dateStr] || 0)
      }
      
      const ctx = this.$refs.dailySpendingChart.getContext('2d')
      new Chart(ctx, {
        type: 'line',
        data: {
          labels: last7Days,
          datasets: [{
            label: 'Daily Spending (₹)',
            data: spending,
            borderColor: 'rgb(75, 192, 192)',
            backgroundColor: 'rgba(75, 192, 192, 0.2)',
            tension: 0.1,
            fill: true
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          scales: {
            y: {
              beginAtZero: true
            }
          }
        }
      })
    },
    
    renderParkingUsageChart() {
      const completedReservations = this.reservations.filter(r => r.status === 'completed')
      
      const lotUsage = {}
      completedReservations.forEach(reservation => {
        lotUsage[reservation.lot_name] = (lotUsage[reservation.lot_name] || 0) + 1
      })
      
      const labels = Object.keys(lotUsage)
      const data = Object.values(lotUsage)
      
      if (labels.length === 0) {
        const ctx = this.$refs.parkingUsageChart.getContext('2d')
        ctx.fillStyle = '#6c757d'
        ctx.textAlign = 'center'
        ctx.font = '14px Arial'
        ctx.fillText('No parking history yet', ctx.canvas.width / 2, ctx.canvas.height / 2)
        return
      }
      
      const ctx = this.$refs.parkingUsageChart.getContext('2d')
      new Chart(ctx, {
        type: 'doughnut',
        data: {
          labels: labels,
          datasets: [{
            data: data,
            backgroundColor: [
              '#FF6384',
              '#36A2EB',
              '#FFCE56',
              '#4BC0C0',
              '#9966FF',
              '#FF9F40'
            ]
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              position: 'bottom'
            }
          }
        }
      })
    },
    
    showReleaseModal(reservation) {
      console.log('Showing release modal for:', reservation)
      this.releaseReservation = reservation
      this.showReleaseModalFlag = true
    },
    
    closeReleaseModal() {
      this.showReleaseModalFlag = false
      this.releaseReservation = null
    },
    
    async confirmRelease() {
      if (!this.releaseReservation) return
      
      this.loading = true
      try {
        console.log('Releasing reservation:', this.releaseReservation.id)
        const response = await axios.post(`/api/release-parking/${this.releaseReservation.id}`)
        
        console.log('✅ Release successful:', response.data)
        this.closeReleaseModal()
        alert('Parking released successfully!')
        
        // Refresh reservations
        await this.loadReservations()
        
      } catch (error) {
        console.error('❌ Release failed:', error)
        alert(error.response?.data?.error || 'Release failed')
      } finally {
        this.loading = false
      }
    },
    
    formatDateTime(dateString) {
      if (!dateString) return 'N/A'
      
      const date = new Date(dateString)
      return date.toLocaleString('en-IN', {
        day: '2-digit',
        month: '2-digit', 
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: true,
        timeZone: 'Asia/Kolkata'
      })
    },
    
    calculateLiveDuration(parkingTime) {
      if (!parkingTime) return '0m'
      
      const start = new Date(parkingTime)
      const now = new Date()
      const diffMs = Math.max(0, now - start)
      
      const hours = Math.floor(diffMs / (1000 * 60 * 60))
      const minutes = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60))
      
      if (hours > 0) {
        return `${hours}h ${minutes}m`
      } else {
        return `${minutes}m`
      }
    },
    
    calculateLiveCost(reservation) {
      if (!reservation.parking_timestamp || !reservation.lot_price) return '0.00'
      
      const start = new Date(reservation.parking_timestamp)
      const now = new Date()
      const hours = Math.max(0, (now - start) / (1000 * 60 * 60))
      
      // Minimum cost for very short durations
      const duration_minutes = (now - start) / (1000 * 60)
      if (duration_minutes < 6) {
        return Math.max(1.0, hours * reservation.lot_price).toFixed(2)
      }
      
      return (hours * reservation.lot_price).toFixed(2)
    },
    
    async logout() {
      try {
        await axios.post('/api/logout')
        this.$router.push('/')
      } catch (error) {
        this.$router.push('/')
      }
    }
  }
}
</script>

<style scoped>
.modal {
  background-color: rgba(0,0,0,0.5);
}

.table th {
  border-top: none;
}

.card {
  transition: transform 0.2s;
}

.card:hover {
  transform: translateY(-2px);
}

.modal-content {
  border-radius: 12px;
  border: none;
  box-shadow: 0 10px 40px rgba(0,0,0,0.2);
}

.modal-header {
  border-radius: 12px 12px 0 0;
  border-bottom: 1px solid #dee2e6;
}
</style>
