# Modern-Application-Development-2
# UrbanPark - Vehicle Parking Web Application

UrbanPark is a modern, full-stack web application designed to streamline the process of finding and managing vehicle parking. It provides a user-friendly interface for vehicle owners to locate and reserve parking spots, and a comprehensive dashboard for administrators to manage the entire parking system.

## Features

### For Users:
- **Find Parking:** Easily search for available parking lots by location.
- **Real-time Availability:** View the number of available spots in each parking lot in real-time.
- **Instant Booking:** Reserve a parking spot with a few clicks and get instant confirmation.
- **Reservation Management:** View active and past parking reservations.
- **Live Cost Calculation:** See the current parking cost for active reservations.
- **Personal Dashboard:** A personalized dashboard with a summary of recent activity and statistics.
- **Data Export:** Export personal parking history to a CSV file.
- **Summary Analytics:** View charts on daily spending and most used parking lots.

### For Admins:
- **Parking Lot Management:** Add, edit, and delete parking lots. The system prevents deletion if spots are occupied.
- **Real-time Dashboard:** A comprehensive dashboard showing statistics like total lots, total spots, available spots, occupied spots, and total users.
- **Live Spot Status:** View the real-time status of each individual parking spot (available or occupied).
- **User Management:** View a list of all registered users.
- **Detailed Spot Information:** Click on any spot to see details, including the occupying vehicle's information if it's booked.
- **System Jobs:** Manually trigger background tasks to send daily reminders or monthly reports to users.
- **Summary Analytics:** Visualize data with charts for available vs. occupied spots and revenue by parking lot.

## Tech Stack

- **Backend:** Flask, Flask-SQLAlchemy, Celery, Redis, Flask-Mail
- **Frontend:** Vue.js, Vue Router, Axios, Chart.js, Bootstrap
- **Database:** SQLite

## Getting Started

### Prerequisites

- Python 3.x
- Node.js and npm
- Redis

### Backend Setup

1.  Navigate to the `backend` directory.
2.  Install the required Python packages:
    ```bash
    pip install -r requirements.txt
    ```
3.  Start the Flask development server:
    ```bash
    flask run
    ```
    The backend will be running at `http://localhost:5000`.

### Frontend Setup

1.  Navigate to the `frontend` directory.
2.  Install the npm dependencies:
    ```bash
    npm install
    ```
3.  Start the Vue development server:
    ```bash
    npm run serve
    ```
    The frontend will be available at `http://localhost:8080`.

## Usage

- **Admin Account:** A default admin user is created with the credentials:
    - **Email:** `admin@parking.com`
    - **Password:** `admin123`
- **User Account:** New users can register through the "Register" page.

## Project Structure
`
/
├── backend/
│   ├── app.py          # Main Flask application
│   └── parking.db      # SQLite database
└── frontend/
    ├── public/
    ├── src/
    │   ├── assets/
    │   ├── components/
    │   ├── router/
    │   ├── views/      # Vue components for pages
    │   └── main.js     # Main Vue application entrypoint
    ├── package.json
    └── ...
`
