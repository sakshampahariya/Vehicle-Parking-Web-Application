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

    <!-- Search Section -->
    <div class="container py-4">
      <div class="card mb-4">
        <div class="card-header">
          <h5 class="mb-0">
            <i class="fas fa-search me-2"></i>Find Parking Spots
          </h5>
        </div>
        <div class="card-body">
          <div class="row">
            <div class="col-md-8">
              <div class="input-group">
                <span class="input-group-text">
                  <i class="fas fa-map-marker-alt"></i>
                </span>
                <input 
                  type="text" 
                  class="form-control" 
                  placeholder="Search by area, city, or location name..."
                  v-model="searchQuery"
                  @input="filterParkingLots"
                >
              </div>
            </div>
            <div class="col-md-4">
              <button class="btn btn-outline-secondary w-100" @click="clearSearch">
                <i class="fas fa-times me-1"></i>Clear Search
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Active Booking Alert -->
      <div v-if="activeReservation" class="alert alert-info mb-4">
        <div class="d-flex justify-content-between align-items-center">
          <div>
            <h5 class="mb-1">🚗 Active Booking</h5>
            <p class="mb-0">
              <strong>Spot ID {{ activeReservation.spot_id }}</strong> at {{ activeReservation.lot_name }} 
              - Vehicle: {{ activeReservation.vehicle_number }}
            </p>
            <small class="text-muted">Parked since: {{ formatDateTime(activeReservation.parking_timestamp) }}</small>
          </div>
          <button class="btn btn-warning" @click="showReleaseModal(activeReservation)">
            <i class="fas fa-sign-out-alt me-1"></i>Release Parking
          </button>
        </div>
      </div>

      <h2 class="mb-4">Available Parking Lots</h2>
      
      <!-- Parking Lots Grid (filtered results) -->
      <div class="row">
        <div class="col-lg-4 mb-4" v-for="lot in filteredParkingLots" :key="lot.id">
          <div class="card h-100">
            <div class="card-header d-flex justify-content-between align-items-center">
              <h5 class="mb-0">{{ lot.prime_location_name }}</h5>
              <span class="badge bg-success">₹{{ lot.price }}/hr</span>
            </div>
            
            <div class="card-body">
              <p class="text-muted mb-2">
                <i class="fas fa-map-marker-alt me-1"></i>{{ lot.address }}
              </p>
              <p class="text-muted mb-3">PIN: {{ lot.pin_code }}</p>
              
              <div class="row text-center mb-3">
                <div class="col">
                  <div class="fw-bold text-success">{{ lot.available_spots }}</div>
                  <small class="text-muted">Available</small>
                </div>
                <div class="col">
                  <div class="fw-bold text-primary">{{ lot.number_of_spots }}</div>
                  <small class="text-muted">Total Spots</small>
                </div>
              </div>
            </div>
            
            <div class="card-footer">
              <button 
                class="btn btn-primary w-100"
                @click="showBookingModal(lot)"
                :disabled="lot.available_spots === 0 || activeReservation"
              >
                <i class="fas fa-car me-1"></i>
                {{ lot.available_spots === 0 ? 'No Spots Available' : 
                   activeReservation ? 'Already Booked' : 'Book Parking' }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Booking Modal -->
    <div class="modal fade" :class="{ show: showBookingModalFlag }" :style="{ display: showBookingModalFlag ? 'block' : 'none' }" tabindex="-1">
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">Book Parking Spot</h5>
            <button type="button" class="btn-close" @click="closeBookingModal"></button>
          </div>
          
          <form @submit.prevent="bookParking">
            <div class="modal-body">
              <div v-if="selectedLot">
                <h6>Parking Lot Details</h6>
                <p><strong>Location:</strong> {{ selectedLot.prime_location_name }}</p>
                <p><strong>Address:</strong> {{ selectedLot.address }}</p>
                <p><strong>Rate:</strong> ₹{{ selectedLot.price }}/hour</p>
                <p><strong>Available Spots:</strong> {{ selectedLot.available_spots }}</p>
                
                <hr>
                
                <div class="mb-3">
                  <label for="vehicle_number" class="form-label">Vehicle Number *</label>
                  <input
                    type="text"
                    class="form-control"
                    id="vehicle_number"
                    v-model="bookingForm.vehicle_number"
                    placeholder="e.g., MH 12 AB 1234"
                    required
                  >
                </div>
              </div>
            </div>
            
            <div class="modal-footer">
              <button type="button" class="btn btn-secondary" @click="closeBookingModal">Cancel</button>
              <button type="submit" class="btn btn-primary" :disabled="loading">
                <span v-if="loading" class="spinner-border spinner-border-sm me-2"></span>
                {{ loading ? 'Booking...' : 'Confirm Booking' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>

    <!-- Booking Success Modal -->
    <div class="modal fade" :class="{ show: showSuccessModal }" :style="{ display: showSuccessModal ? 'block' : 'none' }" tabindex="-1">
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header bg-success text-white">
            <h5 class="modal-title">🎉 Booking Confirmed!</h5>
            <button type="button" class="btn-close btn-close-white" @click="closeSuccessModal"></button>
          </div>
          
          <div class="modal-body" v-if="lastBooking">
            <div class="text-center mb-3">
              <i class="fas fa-check-circle text-success" style="font-size: 3rem;"></i>
            </div>
            
            <div class="row">
              <div class="col-6"><strong>Spot ID:</strong></div>
              <div class="col-6">{{ lastBooking.spot_id }}</div>
            </div>
            <div class="row">
              <div class="col-6"><strong>Location:</strong></div>
              <div class="col-6">{{ lastBooking.parking_lot }}</div>
            </div>
            <div class="row">
              <div class="col-6"><strong>Vehicle:</strong></div>
              <div class="col-6">{{ lastBooking.vehicle_number }}</div>
            </div>
            <div class="row">
              <div class="col-6"><strong>Parked At:</strong></div>
              <div class="col-6">{{ lastBooking.parking_timestamp }}</div>
            </div>
            
            <div class="alert alert-info mt-3">
              <strong>Remember your Spot ID: {{ lastBooking.spot_id }}</strong><br>
              <small>You'll need this when you return to your vehicle.</small>
            </div>
          </div>
          
          <div class="modal-footer">
            <button type="button" class="btn btn-success" @click="closeSuccessModal">Got it!</button>
          </div>
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
                  <td><strong>Vehicle Number:</strong></td>
                  <td>{{ releaseReservation.vehicle_number }}</td>
                </tr>
                <tr>
                  <td><strong>Parking Time:</strong></td>
                  <td>{{ formatDateTime(releaseReservation.parking_timestamp) }}</td>
                </tr>
                <tr>
                  <td><strong>Releasing Time:</strong></td>
                  <td>{{ formatCurrentTime() }}</td>
                </tr>
                <tr>
                  <td><strong>Duration:</strong></td>
                  <td>{{ calculateDuration(releaseReservation.parking_timestamp) }}</td>
                </tr>
                <tr>
                  <td><strong>Total Cost:</strong></td>
                  <td class="fw-bold text-primary">₹{{ calculateCost(releaseReservation.parking_timestamp, releaseReservation.lot_price) }}</td>
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
    <div v-if="showBookingModalFlag || showSuccessModal || showReleaseModalFlag || showChartsModal" class="modal-backdrop fade show"></div>
  </div>
</template>

<script>
import axios from 'axios'
import { Chart, registerables } from 'chart.js'

Chart.register(...registerables)

export default {
  name: 'ParkingLots',
  data() {
    return {
      user: null,
      parkingLots: [],
      filteredParkingLots: [],
      searchQuery: '',
      activeReservation: null,
      selectedLot: null,
      lastBooking: null,
      releaseReservation: null,
      showBookingModalFlag: false,
      showSuccessModal: false,
      showReleaseModalFlag: false,
      loading: false,
      bookingForm: {
        vehicle_number: ''
      },
      // ADDED: Summary modal data
      showChartsModal: false,
      stats: {
        total_bookings: 0,
        active_bookings: 0,
        completed_bookings: 0,
        total_spent: 0
      },
      reservations: []
    }
  },

  async mounted() {
    await this.loadUserInfo()
    await this.loadParkingLots()
    await this.loadActiveReservation()
    await this.loadStats()
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
    
    async loadParkingLots() {
      try {
        const response = await axios.get('/api/parking-lots')
        this.parkingLots = response.data
        this.filteredParkingLots = [...this.parkingLots]
      } catch (error) {
        console.error('Error loading parking lots:', error)
      }
    },

    async loadActiveReservation() {
      try {
        const response = await axios.get('/api/my-reservations')
        const reservations = response.data
        this.activeReservation = reservations.find(r => r.status === 'active')
        
        // FIXED: Use lot_price from the API response
        if (this.activeReservation && this.activeReservation.lot_price) {
          // lot_price is already available from the API
        }
      } catch (error) {
        console.error('Error loading reservations:', error)
      }
    },

    // ADDED: Load stats for summary modal
    async loadStats() {
      try {
        const [statsResponse, reservationsResponse] = await Promise.all([
          axios.get('/api/user-dashboard-stats'),
          axios.get('/api/my-reservations')
        ])
        this.stats = statsResponse.data
        this.reservations = reservationsResponse.data
      } catch (error) {
        console.error('Error loading user stats:', error)
      }
    },

    // Search functionality
    filterParkingLots() {
      if (!this.searchQuery.trim()) {
        this.filteredParkingLots = [...this.parkingLots]
        return
      }

      const query = this.searchQuery.toLowerCase()
      this.filteredParkingLots = this.parkingLots.filter(lot => 
        lot.prime_location_name.toLowerCase().includes(query) ||
        lot.address.toLowerCase().includes(query)
      )
    },

    clearSearch() {
      this.searchQuery = ''
      this.filteredParkingLots = [...this.parkingLots]
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
    
    showBookingModal(lot) {
      this.selectedLot = lot
      this.showBookingModalFlag = true
    },
    
    closeBookingModal() {
      this.showBookingModalFlag = false
      this.selectedLot = null
      this.bookingForm.vehicle_number = ''
    },
    
    // FIXED: Simplified booking method
    async bookParking() {
      if (!this.selectedLot) return
      
      this.loading = true
      try {
        // Find first available spot
        const availableSpot = this.selectedLot.spots.find(spot => spot.status === 'A')
        
        if (!availableSpot) {
          alert('No available spots')
          return
        }
        
        const response = await axios.post(`/api/reserve-parking/${availableSpot.id}`, {
          vehicle_number: this.bookingForm.vehicle_number
        })
        
        // FIXED: Use the EXACT data returned by backend
        this.lastBooking = {
          spot_id: response.data.spot_id,
          parking_lot: response.data.lot_name,
          vehicle_number: response.data.vehicle_number,
          parking_timestamp: response.data.parking_time  // Already formatted by backend
        }
        
        this.closeBookingModal()
        this.showSuccessModal = true
        
        // Refresh data
        await this.loadParkingLots()
        await this.loadActiveReservation()
        
      } catch (error) {
        alert('Booking failed: ' + (error.response?.data?.error || error.message))
      } finally {
        this.loading = false
      }
    },
    
    closeSuccessModal() {
      this.showSuccessModal = false
      this.lastBooking = null
    },
    
    showReleaseModal(reservation) {
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
        await axios.post(`/api/release-parking/${this.releaseReservation.id}`)
        
        this.closeReleaseModal()
        alert('Parking released successfully!')
        
        // Refresh data
        await this.loadParkingLots()
        await this.loadActiveReservation()
        
      } catch (error) {
        alert(error.response?.data?.error || 'Release failed')
      } finally {
        this.loading = false
      }
    },
  
    calculateDuration(parkingTime) {
      if (!parkingTime) return '0m'
      
      const start = new Date(parkingTime)
      const now = new Date()
      const diffMs = now - start
      
      if (diffMs < 0) return '0m'
      
      const hours = Math.floor(diffMs / (1000 * 60 * 60))
      const minutes = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60))
      
      if (hours > 0) {
        return `${hours}h ${minutes}m`
      } else {
        return `${minutes}m`
      }
    },
  
    calculateCost(parkingTime, hourlyRate) {
      if (!parkingTime || !hourlyRate) return '0.00'
      
      const start = new Date(parkingTime)
      const now = new Date()
      const diffMs = now - start
      
      if (diffMs < 0) return '0.00'
      
      const hours = diffMs / (1000 * 60 * 60)
      
      // Only apply minimum if very short duration (less than 6 minutes)
      if (diffMs < 360000) { // 6 minutes in milliseconds
        return Math.max(1.0, hours * hourlyRate).toFixed(2)
      }
      
      return (hours * hourlyRate).toFixed(2)
    },
    
    // FIXED: Consistent date formatting
    formatDateTime(dateString) {
      if (!dateString) return 'N/A'
      
      // If it's already formatted (contains comma), return as is
      if (typeof dateString === 'string' && dateString.includes(',')) {
        return dateString
      }
      
      const date = new Date(dateString)
      return date.toLocaleString('en-IN', {
        day: '2-digit',
        month: '2-digit', 
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: true
      })
    },
    
    formatCurrentTime() {
      const now = new Date()
      return now.toLocaleString('en-IN', {
        day: '2-digit',
        month: '2-digit', 
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: true
      })
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

.alert-info {
  border-left: 4px solid #17a2b8;
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

.card {
  border: none;
  border-radius: 12px;
}
</style>
