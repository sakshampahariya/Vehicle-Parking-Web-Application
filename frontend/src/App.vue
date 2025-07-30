<template>
  <div id="app">
    <router-view />
  </div>
</template>

<script>
export default {
  name: 'App'
}
</script>

<style>
#app {
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

.navbar-brand {
  font-weight: bold;
}

.card {
  box-shadow: 0 2px 4px rgba(0,0,0,.1);
  border: none;
}

.btn {
  border-radius: 6px;
}

.table th {
  border-top: none;
  font-weight: 600;
}

.badge {
  font-size: 0.75rem;
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
}

.spot-available {
  background-color: #28a745;
  color: white;
}

.spot-occupied {
  background-color: #dc3545;
  color: white;
}
</style>
