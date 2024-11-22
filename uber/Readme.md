

# Uber Clone Flask App

This project is a Python Flask-based Uber clone application that replicates the basic functionalities of the Uber service. It allows users to register, create orders, and enables drivers to accept and complete those orders. Real-time communication between users and drivers is facilitated via Socket.IO.

---

## Features

### **User Features**
- **Registration:** Users can sign up and create accounts, with their credentials securely stored in SQLite.
- **Order Creation:** Users can create orders with details including pickup/drop-off locations, time, payment method, and car ride type (e.g., UberX).
- **Driver Assignment:** After requesting a ride, users are assigned a driver in a waiting page where they can see the driver's details and chat in real time.
- **Order Completion:** Once the order status changes to `completed`, users can return to the home page.

### **Driver Features**
- **Registration:** Drivers register with credentials stored in SQLite. Additional driver data (e.g., name, last name, birthdate, car plate) is stored in MongoDB.
- **Order Management:** Drivers can view orders based on their car ride type (e.g., UberX). They can accept orders, changing the status from `searching` to `assigned`.
- **Real-time Communication:** Drivers can chat with users for ongoing orders and view order details.
- **Order Completion:** Upon completing an order, drivers update the status to `completed` and return to the main orders page.

### **Real-Time Chat**
- Users and drivers can communicate during ongoing orders using a chat interface powered by Socket.IO.

### **Order Status Tracking**
- Orders transition through various statuses:
  - **`searching`**: Order is created and awaiting driver assignment.
  - **`assigned`**: A driver has accepted the order.
  - **`completed`**: The order is finished.

---

## Setup Instructions

1. **Create a Virtual Environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the Application**
   ```bash
   python main.py
   ```

---

## Known Issues
- **Admin Portal**: Currently under development.

---

## Authors
- **Atef Fawaz**

---

## Outsourced Services
- **Google Maps API**: For geolocation and route optimization.

- **main_user.html**: You need to get API's from google console so you could show the map : 
Directions API,
Geolocation API,
Google Cloud APIs,
Maps JavaScript API,
Places API,
Geocoding API,
Distance Matrix API.