<template>
  <div>
    <!-- Navigation -->
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
      <div class="container">
        <router-link class="navbar-brand" to="/">UrbanPark</router-link>
        
        <div class="navbar-nav ms-auto">
          <router-link class="nav-link" to="/login">Login</router-link>
          <router-link class="nav-link" to="/register">Register</router-link>
        </div>
      </div>
    </nav>

    <!-- Hero Section -->
    <div class="bg-primary text-white">
      <div class="container py-5">
        <div class="row align-items-center">
          <div class="col-lg-6">
            <h1 class="display-4 fw-bold mb-4">Find & Book Parking Spots Instantly</h1>
            <p class="lead mb-4">Discover available parking spaces near you and reserve them with just a few clicks. Safe, secure, and convenient parking solutions.</p>
            <div class="d-flex gap-3">
              <router-link to="/register" class="btn btn-light btn-lg">Get Started</router-link>
              <router-link to="/login" class="btn btn-outline-light btn-lg">Sign In</router-link>
            </div>
          </div>
          <div class="col-lg-6">
            <div class="text-center">
              <i class="fas fa-car" style="font-size: 200px; opacity: 0.3;"></i>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Features Section -->
    <div class="container py-5">
      <div class="row text-center mb-5">
        <div class="col">
          <h2 class="display-5 fw-bold">Why Choose UrbanPark?</h2>
          <p class="lead text-muted">Simple, efficient, and reliable parking management</p>
        </div>
      </div>
      
      <div class="row g-4">
        <div class="col-md-4">
          <div class="card h-100 text-center border-0">
            <div class="card-body">
              <i class="fas fa-search text-primary mb-3" style="font-size: 3rem;"></i>
              <h4>Find Parking</h4>
              <p class="text-muted">Easily discover available parking spots in your desired location</p>
            </div>
          </div>
        </div>
        
        <div class="col-md-4">
          <div class="card h-100 text-center border-0">
            <div class="card-body">
              <i class="fas fa-mobile-alt text-primary mb-3" style="font-size: 3rem;"></i>
              <h4>Book Instantly</h4>
              <p class="text-muted">Reserve your parking spot with a simple click and get instant confirmation</p>
            </div>
          </div>
        </div>
        
        <div class="col-md-4">
          <div class="card h-100 text-center border-0">
            <div class="card-body">
              <i class="fas fa-shield-alt text-primary mb-3" style="font-size: 3rem;"></i>
              <h4>Secure & Safe</h4>
              <p class="text-muted">All parking areas are monitored and secured for your vehicle's safety</p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Call to Action -->
    <div class="bg-light py-5">
      <div class="container text-center">
        <h3 class="fw-bold mb-4">Ready to Park Smarter?</h3>
        <p class="lead mb-4">Join thousands of users who have made parking hassle-free</p>
        <router-link to="/register" class="btn btn-primary btn-lg">Start Parking Today</router-link>
      </div>
    </div>

    <!-- Footer -->
    <footer class="bg-dark text-white py-4">
      <div class="container">
        <div class="row">
          <div class="col-md-6">
            <h5>UrbanPark</h5>
            <p>Making parking simple and convenient for everyone.</p>
          </div>
          <div class="col-md-6 text-md-end">
            <p>&copy; 2025 UrbanPark. All rights reserved.</p>
            <p>
            Developed by : 
            <a href="https://www.linkedin.com/in/sakshampahariya" target="_blank" style="color: white; text-decoration: none;">
            Saksham Pahariya
            </a>
            </p>
          </div>
        </div>
      </div>
    </footer>

  </div>
</template>

<script>
export default {
  name: 'Home'
}
</script>
