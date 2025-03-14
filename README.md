# Logistics System

A Python-based logistics system for inventory tracking and shipment scheduling with cloud integration.

## Features
- Real-time inventory management
- Shipment scheduling
- Cloud synchronization
- SQLite database persistence

## Setup
1. Clone the repository
2. Create a virtual environment: `python -m venv venv`
3. Activate it: `source venv/bin/activate` (Windows: `venv\Scripts\activate`)
4. Install dependencies: `pip install -r requirements.txt`
5. Run the application: `python src/logistics.py`

## Requirements
- Python 3.8+
- See requirements.txt for dependencies

## Configuration
- Update cloud API endpoint and key in `src/logistics.py`
- Adjust database path in `config/` if needed