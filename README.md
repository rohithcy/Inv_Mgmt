# Logistics Management System

A web-based application for managing inventory and shipments, built with Flask and Firebase. It supports multiple users with isolated data, a graphical dashboard, and real-time syncing, making it ideal for small-scale logistics tracking.

## Overview

The Logistics Management System enables users to register, log in, and manage their own inventory and shipments. Designed as a portfolio project, it showcases full-stack development with Python, Flask, SQLite, and Firebase integration.

### Key Features
- **User Authentication**: Secure registration and login via Firebase Authentication.
- **Inventory Management**: Add, update, and view items (name, quantity, location).
- **Shipment Scheduling**: Schedule shipments with automatic inventory updates.
- **Graphical Dashboard**: Responsive card-based UI with hover effects.
- **Multi-User Support**: Data isolation per user using SQLite and Firebase.
- **Data Reset**: Clear personal inventory and shipments.
- **Deployment Ready**: Configured for hosting on Render.

### Technologies Used
- **Backend**: Python 3.13, Flask 2.3.3, SQLite, Firebase Admin SDK 6.5.0
- **Frontend**: HTML, CSS, Jinja2
- **Deployment**: Gunicorn 23.0.0, Render
- **Other**: Logging, UUID, real-time database syncing

## Prerequisites

- Python 3.13.2 (or compatible 3.x version)
- Git
- Firebase project with Realtime Database and Authentication (Email/Password) enabled
- GitHub account for deployment

## Installation

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/rohithcy/LogiMgmt.git
   cd LogiMgmt

2. **python3 -m venv venv**:
source venv/bin/activate  # On Windows: venv\Scripts\activate

3. pip install -r requirements.txt

4. **Configure Firebase**:
    Create a Firebase project at console.firebase.google.com.
    Enable Authentication (Email/Password) and Realtime Database.
    Download serviceAccountKey.json from Project Settings > Service Accounts.
    Place it in config/serviceAccountKey.json.
    Update logistics.py with your database URL if different: firebase_admin.initialize_app(cred, {'databaseURL': 'https://your-project-id.firebaseio.com/'})

5. **Run Locally**:
   python3 src/app.py
   Access at http://127.0.0.1:5000
   