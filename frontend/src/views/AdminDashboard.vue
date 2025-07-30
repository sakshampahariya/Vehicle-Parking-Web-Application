<template>
  <div>
    <!-- Navbar -->
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark sticky-top">
      <div class="container">
        <!-- Left side: Logo -->
        <router-link class="navbar-brand fw-bold" to="/admin">UrbanPark</router-link>

        <!-- Right side menu -->
        <div class="d-flex align-items-center gap-3">
          <button class="btn btn-link text-light text-decoration-none" @click="showUsersModal = true">Users</button>
          <button class="btn btn-link text-light text-decoration-none" @click="toggleSearchPanel">Search</button>
          <button class="btn btn-link text-light text-decoration-none" @click="showSummaryModal">Summary</button>

          <!-- System Jobs dropdown -->
          <div class="nav-item dropdown text-light">
            <a
              class="nav-link dropdown-toggle"
              href="#"
              role="button"
              data-bs-toggle="dropdown"
              aria-expanded="false"
            >
              System Jobs
            </a>
            <ul class="dropdown-menu dropdown-menu-end">
              <li><button class="dropdown-item" @click="triggerDailyReminders">Send Daily Reminder</button></li>
              <li><button class="dropdown-item" @click="triggerMonthlyReports">Send Monthly Report</button></li>
            </ul>
          </div>

          <button class="btn btn-outline-danger btn-sm" @click="logout">Logout</button>
        </div>
      </div>
    </nav>

    <!-- Search panel -->
    <div v-if="showSearchPanel" class="container mt-3">
      <div class="card">
        <div class="card-body">
          <h5 class="card-title">Search Parking Lots</h5>
          <div class="input-group mb-3">
            <input
              type="text"
              class="form-control"
              placeholder="Search by location name..."
              v-model="searchQuery"
              @input="searchLots"
            />
            <button class="btn btn-outline-secondary" @click="clearSearch"><i class="fas fa-times"></i></button>
          </div>

          <div v-if="searchResults.length > 0">
            <h6>Search Results</h6>
            <div class="list-group">
              <button
                v-for="lot in searchResults"
                :key="lot.id"
                class="list-group-item list-group-item-action"
                @click="scrollToLot(lot.id); toggleSearchPanel()"
              >
                <strong>{{ lot.prime_location_name }}</strong><br />
                <small class="text-muted">{{ lot.address }}</small>
              </button>
            </div>
          </div>

          <div v-else-if="searchQuery.trim() !== ''" class="text-muted">No results found.</div>
        </div>
      </div>
    </div>

    <!-- Heading Box: Parking Lots Title -->
    <div class="container my-4">
      <div class="d-flex justify-content-center">
        <div class="p-3 bg-light border rounded shadow-sm w-auto">
          <h2 class="mb-0">Parking Lots</h2>
        </div>
      </div>
    </div>

    <!-- Parking Lots Grid -->
    <div class="container">
      <div class="row">
        <div
          class="col-lg-4 mb-4"
          v-for="lot in displayedLots"
          :key="lot.id"
          :id="'lot-' + lot.id"
        >
          <div class="card h-100">
            <div class="card-header d-flex justify-content-between align-items-center">
              <h5 class="mb-0">{{ lot.prime_location_name }}</h5>
              <span class="badge bg-primary">₹{{ lot.price }}/hr</span>
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
                  <div class="fw-bold text-warning">{{ lot.occupied_spots }}</div>
                  <small class="text-muted">Occupied</small>
                </div>
                <div class="col">
                  <div class="fw-bold text-primary">{{ lot.number_of_spots }}</div>
                  <small class="text-muted">Total</small>
                </div>
              </div>

              <!-- Parking Spots Grid -->
              <div class="mb-3">
                <small class="text-muted">Spot Status (Click on spot for details):</small>
                <div class="d-flex flex-wrap mt-1">
                  <div
                    v-for="spot in lot.spots"
                    :key="spot.id"
                    class="parking-spot cursor-pointer"
                    :class="spot.status === 'A' ? 'spot-available' : 'spot-occupied'"
                    :title="`Spot ${spot.spot_number}: ${spot.status === 'A' ? 'Available' : 'Occupied'} - Click for details`"
                    @click="showSpotDetails(spot.id)"
                  >
                    {{ spot.spot_number }}
                  </div>
                </div>
              </div>
            </div>

            <div class="card-footer d-flex gap-2">
              <button class="btn btn-outline-primary btn-sm flex-fill" @click="editLot(lot)">
                <i class="fas fa-edit me-1"></i>Edit
              </button>
              <button
                class="btn btn-outline-danger btn-sm flex-fill"
                @click="deleteLot(lot)"
                :disabled="lot.occupied_spots > 0"
                :title="lot.occupied_spots > 0 ? 'Cannot delete lot with occupied spots' : 'Delete parking lot'"
              >
                <i class="fas fa-trash me-1"></i>Delete
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="container mb-4">
      <div class="d-flex justify-content-center">
        <button class="btn btn-primary" @click="showAddModal = true">
          <i class="fas fa-plus me-2"></i>Add New Lot
        </button>
      </div>
    </div>

    <!-- Spot Details Modal -->
    <div
      class="modal fade"
      :class="{ show: showSpotModal }"
      :style="{ display: showSpotModal ? 'block' : 'none' }"
      tabindex="-1"
      aria-modal="true"
      role="dialog"
    >
      <div class="modal-dialog modal-lg">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">Spot Details</h5>
            <button type="button" class="btn-close" @click="closeSpotModal"></button>
          </div>

          <div class="modal-body" v-if="selectedSpot">
            <div v-if="selectedSpot.status === 'A'" class="col-12">
              <h6>Spot Information</h6>
              <table class="table table-sm">
                <tbody>
                  <tr><td><strong>Spot ID</strong></td><td>{{ selectedSpot.id }}</td></tr>
                  <tr><td><strong>Spot Number</strong></td><td>{{ selectedSpot.spot_number }}</td></tr>
                  <tr><td><strong>Status</strong></td><td><span class="badge bg-success">Available</span></td></tr>
                  <tr><td><strong>Parking Lot</strong></td><td>{{ selectedSpot.lot_name }}</td></tr>
                </tbody>
              </table>
            </div>
            <div v-else class="row">
              <div class="col-md-6">
                <h6>Spot Information</h6>
                <table class="table table-sm">
                  <tbody>
                    <tr><td><strong>Spot ID</strong></td><td>{{ selectedSpot.id }}</td></tr>
                    <tr><td><strong>Spot Number</strong></td><td>{{ selectedSpot.spot_number }}</td></tr>
                    <tr><td><strong>Status</strong></td><td><span class="badge bg-warning">Occupied</span></td></tr>
                    <tr><td><strong>Parking Lot</strong></td><td>{{ selectedSpot.lot_name }}</td></tr>
                  </tbody>
                </table>
              </div>
              <div v-if="selectedSpot.reservation" class="col-md-6">
                <h6>Occupation Details</h6>
                <table class="table table-sm">
                  <tbody>
                    <tr><td><strong>Customer ID</strong></td><td>{{ selectedSpot.reservation.user_id }}</td></tr>
                    <tr><td><strong>Customer Name</strong></td><td>{{ selectedSpot.reservation.user_name }}</td></tr>
                    <tr><td><strong>Email</strong></td><td>{{ selectedSpot.reservation.user_email }}</td></tr>
                    <tr><td><strong>Vehicle Number</strong></td><td>{{ selectedSpot.reservation.vehicle_number }}</td></tr>
                    <tr><td><strong>Parking Time</strong></td><td>{{ formatDateTime(selectedSpot.reservation.parking_timestamp) }}</td></tr>
                    <tr><td><strong>Hours Parked</strong></td><td>{{ selectedSpot.reservation.hours_parked }}h</td></tr>
                    <tr><td><strong>Estimated Cost</strong></td><td>₹{{ selectedSpot.reservation.estimated_cost }}</td></tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" @click="closeSpotModal">Close</button>
            <button v-if="selectedSpot && selectedSpot.status === 'A'" type="button" class="btn btn-danger" @click="deleteSpot(selectedSpot.id)">
              <i class="fas fa-trash me-1"></i>Delete Spot
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Users Modal -->
    <div
      class="modal fade"
      :class="{ show: showUsersModal }"
      :style="{ display: showUsersModal ? 'block' : 'none' }"
      tabindex="-1"
    >
      <div class="modal-dialog modal-xl">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">All Users</h5>
            <button type="button" class="btn-close" @click="closeUsersModal"></button>
          </div>

          <div class="modal-body">
            <div class="table-responsive">
              <table class="table table-hover">
                <thead>
                  <tr>
                    <th>ID</th><th>Email</th><th>Full Name</th><th>Phone</th><th>Address</th><th>PIN Code</th><th>Joined</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="user in allUsers" :key="user.id">
                    <td>{{ user.id }}</td>
                    <td>{{ user.email }}</td>
                    <td>{{ user.full_name }}</td>
                    <td>{{ user.phone }}</td>
                    <td>{{ user.address }}</td>
                    <td>{{ user.pin_code }}</td>
                    <td>{{ formatDate(user.created_at) }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" @click="closeUsersModal">Close</button>
          </div>
        </div>
      </div>
    </div>

    <!-- Charts Modal -->
    <div
      class="modal fade"
      :class="{ show: showChartsModal }"
      :style="{ display: showChartsModal ? 'block' : 'none' }"
      tabindex="-1"
    >
      <div class="modal-dialog modal-xl">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">Summary Analytics</h5>
            <button type="button" class="btn-close" @click="closeChartsModal"></button>
          </div>

          <div class="modal-body">
            <div class="row">
              <div class="col-md-6">
                <h6>Available vs Occupied Spots</h6>
                <div style="position: relative; height: 400px;">
                  <canvas ref="barChart"></canvas>
                </div>
              </div>
              <div class="col-md-6">
                <h6>Revenue by Parking Lot</h6>
                <div style="position: relative; height: 400px;">
                  <canvas ref="pieChart"></canvas>
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

    <!-- Add/Edit Parking Lot Modal -->
    <div
      class="modal fade"
      :class="{ show: showAddModal || showEditModal }"
      :style="{ display: showAddModal || showEditModal ? 'block' : 'none' }"
      tabindex="-1"
    >
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">{{ isEditing ? "Edit" : "Add" }} Parking Lot</h5>
            <button type="button" class="btn-close" @click="closeModal"></button>
          </div>

          <form @submit.prevent="saveLot">
            <div class="modal-body">
              <div class="mb-3">
                <label for="prime_location_name" class="form-label">Location Name *</label>
                <input
                  type="text"
                  class="form-control"
                  id="prime_location_name"
                  v-model="lotForm.prime_location_name"
                  required
                />
              </div>

              <div class="mb-3">
                <label for="address" class="form-label">Address *</label>
                <textarea
                  class="form-control"
                  id="address"
                  rows="2"
                  v-model="lotForm.address"
                  required
                ></textarea>
              </div>

              <div class="row">
                <div class="col-md-6">
                  <div class="mb-3">
                    <label for="pin_code" class="form-label">PIN Code *</label>
                    <input
                      type="text"
                      class="form-control"
                      id="pin_code"
                      v-model="lotForm.pin_code"
                      required
                    />
                  </div>
                </div>
                <div class="col-md-6">
                  <div class="mb-3">
                    <label for="price" class="form-label">Price Per Hour (₹) *</label>
                    <input
                      type="number"
                      step="0.01"
                      class="form-control"
                      id="price"
                      v-model="lotForm.price"
                      min="0"
                      required
                    />
                  </div>
                </div>
              </div>

              <div class="mb-3">
                <label for="number_of_spots" class="form-label">Number of Spots *</label>
                <input
                  type="number"
                  class="form-control"
                  id="number_of_spots"
                  v-model="lotForm.number_of_spots"
                  min="1"
                  max="100"
                  required
                />
              </div>
            </div>

            <div class="modal-footer">
              <button type="button" class="btn btn-secondary" @click="closeModal">Cancel</button>
              <button type="submit" class="btn btn-primary" :disabled="loading">
                <span v-if="loading" class="spinner-border spinner-border-sm me-2"></span>
                {{ loading ? "Saving..." : "Save" }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>

    <!-- Modal Backdrop -->
    <div v-if="showSpotModal || showUsersModal || showChartsModal || showAddModal || showEditModal" class="modal-backdrop fade show"></div>
  </div>
</template>

<script>
import axios from "axios";
import { Chart, registerables } from "chart.js";

Chart.register(...registerables);

export default {
  name: "AdminDashboard",
  data() {
    return {
      user: null,
      stats: {
        total_lots: 0,
        total_spots: 0,
        available_spots: 0,
        occupied_spots: 0,
        total_users: 0,
      },
      parkingLots: [],
      allUsers: [],
      searchQuery: "",
      searchResults: [],
      selectedSpot: null,
      chartsData: null,
      showSpotModal: false,
      showUsersModal: false,
      showChartsModal: false,
      showAddModal: false,
      showEditModal: false,
      isEditing: false,
      editingLotId: null,
      loading: false,
      lotForm: {
        prime_location_name: "",
        address: "",
        pin_code: "",
        price: "",
        number_of_spots: "",
      },
      showSearchPanel: false,
      refreshInterval: null, // Auto-refresh interval
    };
  },
  computed: {
    displayedLots() {
      return this.searchQuery ? this.searchResults : this.parkingLots;
    },
  },
  async mounted() {
    await this.loadUserInfo();
    await this.loadStats();
    await this.loadParkingLots();
    await this.loadAllUsers();
    
    // Auto-refresh every 10 seconds to show real-time updates
    this.refreshInterval = setInterval(() => {
      this.loadParkingLots();
      this.loadStats();
    }, 10000);
  },
  beforeDestroy() {
    if (this.refreshInterval) {
      clearInterval(this.refreshInterval);
    }
  },
  methods: {
    // IST timezone convertor
    toIST(date) {
      if (!(date instanceof Date)) date = new Date(date);
      const utc = date.getTime() + date.getTimezoneOffset() * 60000;
      const istOffset = 5.5 * 60 * 60 * 1000; // IST offset in milliseconds
      return new Date(utc + istOffset);
    },

    // Formatter to datetime to display in IST
    formatDateTime(datetimeStr) {
      if (!datetimeStr) return "";
      const date = new Date(datetimeStr);
      // Use IST timezone for consistent display
      return date.toLocaleString("en-IN", {
        day: "2-digit",
        month: "numeric", 
        year: "numeric",
        hour: "numeric",
        minute: "numeric",
        second: "numeric",
        hour12: true,
        timeZone: "Asia/Kolkata",
      });
    },

    // Calculate hours parked using IST times correctly
    getDisplayedHoursParked(parkingTimestamp) {
      if (!parkingTimestamp) return "0.0";
      const parkingTime = this.toIST(new Date(parkingTimestamp));
      const now = this.toIST(new Date());
      const durationMs = now - parkingTime;
      const hours = durationMs / (1000 * 60 * 60);
      return hours > 0 ? hours.toFixed(1) : "0.0";
    },

    // Calculate estimated cost based on hours and price
    getEstimatedCost(hours, price) {
      const h = parseFloat(hours);
      const p = parseFloat(price);
      if (isNaN(h) || isNaN(p) || h <= 0) return "0.00";
      return (h * p).toFixed(2);
    },

    async loadUserInfo() {
      try {
        const response = await axios.get("/api/me");
        this.user = response.data.user;
      } catch (error) {
        console.error("Error loading user info:", error);
      }
    },

    async loadStats() {
      try {
        const response = await axios.get("/api/admin/dashboard-stats");
        this.stats = response.data;
      } catch (error) {
        console.error("Error loading admin stats:", error);
        this.stats = {
          total_lots: 0,
          total_spots: 0,
          available_spots: 0,
          occupied_spots: 0,
          total_users: 0,
        };
      }
    },

    async loadParkingLots() {
      try {
        const timestamp = new Date().getTime();
        const response = await axios.get(`/api/admin/parking-lots?_t=${timestamp}`);
        this.parkingLots = response.data;
      } catch (error) {
        console.error("Error loading parking lots:", error);
      }
    },

    async loadAllUsers() {
      try {
        const response = await axios.get("/api/admin/users");
        this.allUsers = response.data;
      } catch (error) {
        console.error("Error loading users:", error);
      }
    },

    async searchLots() {
      if (!this.searchQuery.trim()) {
        this.searchResults = [];
        return;
      }
      try {
        const response = await axios.get(
          `/api/admin/search-lots?q=${encodeURIComponent(this.searchQuery)}`
        );
        this.searchResults = response.data;
      } catch (error) {
        console.error("Error searching lots:", error);
      }
    },

    clearSearch() {
      this.searchQuery = "";
      this.searchResults = [];
    },

    scrollToLot(lotId) {
      const el = document.getElementById(`lot-${lotId}`);
      if (el) {
        el.scrollIntoView({ behavior: "smooth", block: "center" });
        el.style.border = "3px solid #007bff";
        setTimeout(() => {
          el.style.border = "";
        }, 3000);
      }
    },

    showSpotDetails(spotId) {
      axios
        .get(`/api/admin/spot-details/${spotId}`)
        .then((response) => {
          this.selectedSpot = response.data;
          this.showSpotModal = true;
        })
        .catch((error) => {
          alert(error.response?.data?.error || "Error loading spot details");
        });
    },

    deleteSpot(spotId) {
      if (confirm("Are you sure you want to delete this spot?")) {
        axios
          .delete(`/api/admin/spots/${spotId}`)
          .then(() => {
            this.closeSpotModal();
            this.loadParkingLots();
            this.loadStats();
            alert("Spot deleted successfully");
          })
          .catch((error) => {
            alert(error.response?.data?.error || "Error deleting spot");
          });
      }
    },

    async loadChartsData() {
      try {
        const response = await axios.get("/api/admin/charts-data");
        this.chartsData = response.data;
      } catch (error) {
        console.error("Error loading charts data:", error);
      }
    },

    async showSummaryModal() {
      await this.loadChartsData();
      this.showChartsModal = true;
      this.$nextTick(() => {
        setTimeout(() => this.renderCharts(), 300);
      });
    },

    renderCharts() {
      if (!this.chartsData) return;

      this.$nextTick(() => {
        const existingBarChart = Chart.getChart(this.$refs.barChart);
        if (existingBarChart) existingBarChart.destroy();
        const existingPieChart = Chart.getChart(this.$refs.pieChart);
        if (existingPieChart) existingPieChart.destroy();

        const barCtx = this.$refs.barChart.getContext("2d");
        new Chart(barCtx, {
          type: "bar",
          data: {
            labels: this.chartsData.bar_chart.labels,
            datasets: [
              {
                label: "Available Spots",
                data: this.chartsData.bar_chart.available,
                backgroundColor: "rgba(40, 167, 69, 0.8)",
                borderColor: "rgba(40, 167, 69, 1)",
                borderWidth: 1,
              },
              {
                label: "Occupied Spots",
                data: this.chartsData.bar_chart.occupied,
                backgroundColor: "rgba(255, 193, 7, 0.8)",
                borderColor: "rgba(255, 193, 7, 1)",
                borderWidth: 1,
              },
            ],
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: { y: { beginAtZero: true } },
          },
        });

        const pieCtx = this.$refs.pieChart.getContext("2d");
        new Chart(pieCtx, {
          type: "pie",
          data: {
            labels: this.chartsData.pie_chart.labels,
            datasets: [
              {
                data: this.chartsData.pie_chart.revenue,
                backgroundColor: [
                  "#FF6384",
                  "#36A2EB",
                  "#FFCE56",
                  "#4BC0C0",
                  "#9966FF",
                  "#FF9F40",
                ],
              },
            ],
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { position: "bottom" } },
          },
        });
      });
    },

    closeSpotModal() {
      this.showSpotModal = false;
      this.selectedSpot = null;
    },

    closeUsersModal() {
      this.showUsersModal = false;
    },

    async closeChartsModal() {
      this.showChartsModal = false;
      Chart.getChart(this.$refs.barChart)?.destroy();
      Chart.getChart(this.$refs.pieChart)?.destroy();
    },

    formatDate(dateStr) {
      if (!dateStr) return "";
      return new Date(dateStr).toLocaleDateString("en-IN");
    },

    editLot(lot) {
      this.isEditing = true;
      this.editingLotId = lot.id;
      this.lotForm = {
        prime_location_name: lot.prime_location_name,
        address: lot.address,
        pin_code: lot.pin_code,
        price: lot.price,
        number_of_spots: lot.number_of_spots,
      };
      this.showEditModal = true;
    },

    async deleteLot(lot) {
      if (lot.occupied_spots > 0) {
        alert("Cannot delete parking lot with occupied spots");
        return;
      }
      if (confirm(`Are you sure you want to delete "${lot.prime_location_name}"?`)) {
        try {
          await axios.delete(`/api/admin/parking-lots/${lot.id}`);
          await this.loadParkingLots();
          await this.loadStats();
          alert("Parking lot deleted successfully");
        } catch (error) {
          alert(error.response?.data?.error || "Error deleting parking lot");
        }
      }
    },

    async saveLot() {
      this.loading = true;
      try {
        if (this.isEditing) {
          await axios.put(`/api/admin/parking-lots/${this.editingLotId}`, this.lotForm);
          alert("Parking lot updated successfully");
        } else {
          await axios.post("/api/admin/parking-lots", this.lotForm);
          alert("Parking lot created successfully");
        }
        this.closeModal();
        await this.loadParkingLots();
        await this.loadStats();
      } catch (error) {
        alert(error.response?.data?.error || "Error saving parking lot");
      } finally {
        this.loading = false;
      }
    },

    closeModal() {
      this.showAddModal = false;
      this.showEditModal = false;
      this.isEditing = false;
      this.editingLotId = null;
      this.lotForm = {
        prime_location_name: "",
        address: "",
        pin_code: "",
        price: "",
        number_of_spots: "",
      };
    },

    async triggerDailyReminders() {
      try {
        const response = await axios.post("/api/admin/trigger-daily-reminders");
        alert(response.data.message);
        console.log("Daily reminders started, task ID:", response.data.task_id);
      } catch (error) {
        alert("Error starting daily reminders: " + (error.response?.data?.error || error.message));
      }
    },

    async triggerMonthlyReports() {
      try {
        const response = await axios.post("/api/admin/trigger-monthly-reports");
        alert(response.data.message);
        console.log("Monthly reports started, task ID:", response.data.task_id);
      } catch (error) {
        alert("Error starting monthly reports: " + (error.response?.data?.error || error.message));
      }
    },

    async logout() {
      try {
        await axios.post("/api/logout");
      } finally {
        this.$router.push("/");
      }
    },

    toggleSearchPanel() {
      this.showSearchPanel = !this.showSearchPanel;
      if (!this.showSearchPanel) this.clearSearch();
    },
  },
  watch: {
    showChartsModal(newVal) {
      if (newVal) this.showSummaryModal();
    },
  },
};
</script>


<style scoped>
.cursor-pointer {
  cursor: pointer;
}
.parking-spot {
  width: 40px;
  height: 40px;
  margin: 2px;
  border-radius: 4px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  font-size: 12px;
  transition: all 0.2s ease;
}
.parking-spot:hover {
  transform: scale(1.1);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}
.spot-available {
  background-color: #28a745;
  color: white;
}
.spot-occupied {
  background-color: #dc3545;
  color: white;
}
.modal {
  background-color: rgba(0, 0, 0, 0.5);
}
.table-responsive {
  max-height: 400px;
  overflow-y: auto;
}
</style>
