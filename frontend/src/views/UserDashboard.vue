<template>
  <div>
    <!-- Navbar (Admin Dashboard Style) -->
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
      <!-- Welcome Section with Export Button -->
      <div class="row mb-4">
        <div class="col-md-8">
          <div class="welcome-section">
            <h2 class="mb-1">Welcome, {{ user?.full_name }}! 👋</h2>
            <p class="text-muted mb-0">Here's your parking dashboard overview</p>
          </div>
        </div>
        <div class="col-md-4 text-end">
          <button 
            class="btn btn-primary btn-lg"
            @click="triggerCSVExport"
            :disabled="exportLoading"
          >
            <span v-if="exportLoading" class="spinner-border spinner-border-sm me-2"></span>
            <i v-else class="fas fa-download me-2"></i>
            {{ exportLoading ? 'Preparing...' : 'Export Data as CSV' }}
          </button>
        </div>
      </div>

      <!-- Recent Parking Table -->
      <div class="card shadow-sm">
        <div class="card-header bg-gradient-primary text-white">
          <div class="d-flex justify-content-between align-items-center">
            <h5 class="mb-0">
              <i class="fas fa-history me-2"></i>Recent Parking Activity
            </h5>
            <span class="badge bg-light text-primary">{{ recentReservations.length }} Recent</span>
          </div>
        </div>
        <div class="card-body">
          <!-- Active Booking Alert -->
          <div v-if="activeReservation" class="alert alert-warning border-warning mb-4">
            <div class="d-flex justify-content-between align-items-center">
              <div>
                <h6 class="mb-1">
                  <i class="fas fa-car text-warning me-2"></i>Active Parking Session
                </h6>
                <p class="mb-0">
                  <strong>Spot {{ activeReservation.spot_id }}</strong> at {{ activeReservation.lot_name }}
                  <br><small class="text-muted">Started: {{ formatDateTime(activeReservation.parking_timestamp) }}</small>
                </p>
              </div>
              <div class="text-end">
                <div class="text-warning fw-bold mb-2">
                  Duration: {{ calculateCurrentDuration(activeReservation.parking_timestamp) }}
                </div>
                <router-link to="/my-reservations" class="btn btn-warning btn-sm">
                  <i class="fas fa-eye me-1"></i>View Details
                </router-link>
              </div>
            </div>
          </div>

          <!-- Recent Activity Table -->
          <div v-if="recentReservations.length === 0" class="text-center py-5">
            <i class="fas fa-car fa-4x text-muted mb-3"></i>
            <h5 class="text-muted">No Recent Parking Activity</h5>
            <p class="text-muted">Ready to find your perfect parking spot?</p>
            <router-link to="/parking-lots" class="btn btn-primary btn-lg">
              <i class="fas fa-search me-2"></i>Find Parking Now
            </router-link>
          </div>
          
          <div v-else class="table-responsive">
            <table class="table table-hover align-middle">
              <thead class="table-light">
                <tr>
                  <th>Spot ID</th>
                  <th>Location</th>
                  <th>Date</th>
                  <th>Duration</th>
                  <th>Cost</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="reservation in recentReservations" :key="reservation.id">
                  <td><span class="badge bg-secondary">{{ reservation.spot_id }}</span></td>
                  <td>
                    <strong>{{ reservation.lot_name }}</strong><br>
                    <small class="text-muted">{{ reservation.lot_address }}</small>
                  </td>
                  <td>{{ formatDate(reservation.parking_timestamp) }}</td>
                  <td>{{ displayDuration(reservation) }}</td>
                  <td>
                    <span v-if="reservation.status === 'completed'" class="fw-bold text-success">
                      ₹{{ displayCost(reservation) }}
                    </span>
                    <span v-else class="text-muted">{{ calculateCurrentDuration(reservation.parking_timestamp) }}</span>
                  </td>
                  <td>
                    <span class="badge" :class="reservation.status === 'active' ? 'bg-warning' : 'bg-success'">
                      {{ reservation.status === 'active' ? 'Active' : 'Completed' }}
                    </span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- View All Button -->
          <div v-if="recentReservations.length > 0" class="text-center mt-3">
            <router-link to="/my-reservations" class="btn btn-outline-primary">
              <i class="fas fa-list me-2"></i>View All Bookings
            </router-link>
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
    <div v-if="showChartsModal" class="modal-backdrop fade show"></div>
  </div>
</template>

<script>
import axios from 'axios'
import { Chart, registerables } from 'chart.js'

Chart.register(...registerables)

export default {
  name: 'UserDashboard',
  data() {
    return {
      user: null,
      stats: {
        total_bookings: 0,
        active_bookings: 0,
        completed_bookings: 0,
        total_spent: 0
      },
      reservations: [],
      activeReservation: null,
      exportJobs: [],
      exportLoading: false,
      showChartsModal: false
    }
  },
  computed: {
    recentReservations() {
      return this.reservations.slice(0, 8)
    }
  },
  async mounted() {
    await this.loadUserInfo()
    await this.loadStats()
    await this.loadReservations()
    await this.loadExportJobs()
  },
  methods: {
    async loadUserInfo() {
      try {
        const response = await axios.get('/api/me')
        this.user = response.data.user
      } catch (error) {
        this.$router.push('/login')
      }
    },
    
    async loadStats() {
      try {
        const response = await axios.get('/api/user-dashboard-stats')
        this.stats = response.data
      } catch (error) {
        console.error('Error loading stats:', error)
      }
    },
    
    async loadReservations() {
      try {
        const response = await axios.get('/api/my-reservations')
        this.reservations = response.data
        this.activeReservation = this.reservations.find(r => r.status === 'active')
      } catch (error) {
        console.error('Error loading reservations:', error)
      }
    },
    
    async loadExportJobs() {
      try {
        const response = await axios.get('/api/my-export-jobs')
        this.exportJobs = response.data
      } catch (error) {
        console.error('Error loading export jobs:', error)
      }
    },
    
    async triggerCSVExport() {
      this.exportLoading = true
      try {
        const response = await axios.post('/api/export-csv')
        alert('✅ CSV export started! You will receive an email when ready.')
        await this.loadExportJobs()
      } catch (error) {
        alert('❌ ' + (error.response?.data?.error || 'Export failed'))
      } finally {
        this.exportLoading = false
      }
    },

    // Summary Modal Functions (Admin Dashboard Style)
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
    
    formatDate(dateString) {
      if (!dateString) return 'N/A'
      
      const date = new Date(dateString)
      return date.toLocaleDateString('en-IN', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric'
      })
    },
    
    displayDuration(reservation) {
      return reservation.duration_display || 'N/A'
    },
    
    displayCost(reservation) {
      if (reservation.status === 'completed') {
        return reservation.parking_cost ? reservation.parking_cost.toFixed(2) : '0.00'
      } else {
        return 'Ongoing'
      }
    },
    
    calculateCurrentDuration(parkingTime) {
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
.bg-gradient-primary {
  background: linear-gradient(135deg, #007bff, #0056b3);
}

.welcome-section {
  padding: 1rem 0;
}

.welcome-section h2 {
  color: #2c3e50;
  font-weight: 600;
}

.card {
  border: none;
  border-radius: 12px;
}

.card-header {
  border-radius: 12px 12px 0 0 !important;
}

.alert {
  border-radius: 12px;
  border-left: 4px solid;
}

.badge {
  font-size: 0.8em;
  padding: 0.5em 0.8em;
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

.btn {
  border-radius: 8px;
  font-weight: 500;
}

.btn-lg {
  padding: 0.75rem 1.5rem;
  font-size: 1.1rem;
}

.table th {
  font-weight: 600;
  color: #495057;
  border-top: none;
}

.shadow-sm {
  box-shadow: 0 0.125rem 0.25rem rgba(0, 0, 0, 0.075) !important;
}

.modal {
  background-color: rgba(0, 0, 0, 0.5);
}

@media (max-width: 768px) {
  .welcome-section h2 {
    font-size: 1.5rem;
  }
  
  .table-responsive {
    font-size: 0.9rem;
  }
}
</style>
