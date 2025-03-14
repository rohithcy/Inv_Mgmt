from flask import Flask, request, render_template, redirect, url_for, session, flash
from logistics import LogisticsSystem, DatabaseManager, CloudSync, auth, db
import uuid
import datetime
import sqlite3
import logging

app = Flask(__name__)
app.secret_key = "your-secret-key-here"
db_manager = DatabaseManager("config/logistics.db")
cloud_sync = CloudSync()

# User authentication functions
def register_user(email: str, password: str) -> bool:
    try:
        auth.create_user(email=email, password=password)
        logging.info(f"User registered: {email}")
        return True
    except Exception as e:
        logging.error(f"Registration failed: {str(e)}")
        return False

def login_user(email: str, password: str) -> bool:
    try:
        user = auth.get_user_by_email(email)
        session['user'] = email
        logging.info(f"User logged in: {email}")
        return True
    except Exception as e:
        logging.error(f"Login failed: {str(e)}")
        return False

def reset_database(user_id: str):
    try:
        with sqlite3.connect("config/logistics.db") as conn:
            conn.execute("DELETE FROM inventory WHERE user_id = ?", (user_id,))
            conn.execute("DELETE FROM shipments WHERE user_id = ?", (user_id,))
            conn.commit()
        logging.info(f"SQLite database cleared for user {user_id}")
    except Exception as e:
        logging.error(f"Failed to clear SQLite for user {user_id}: {str(e)}")

    try:
        ref = db.reference(f'inventory/{user_id}')
        ref.delete()
        logging.info(f"Firebase inventory cleared for user {user_id}")
    except Exception as e:
        logging.error(f"Failed to clear Firebase for user {user_id}: {str(e)}")

@app.route('/')
def home():
    if 'user' not in session:
        return redirect(url_for('login'))
    logistics = LogisticsSystem(db_manager, cloud_sync, session['user'])
    return render_template('home.html', 
                         inventory=logistics.get_inventory_status(),
                         shipments=logistics.get_shipments())

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        if login_user(email, password):
            return redirect(url_for('home'))
        flash("Login failed. Check your credentials.")
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        if register_user(email, password):
            flash("Registration successful. Please log in.")
            return redirect(url_for('login'))
        flash("Registration failed. Try a different email.")
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    logging.info("User logged out")
    return redirect(url_for('login'))

@app.route('/add_inventory', methods=['GET', 'POST'])
def add_inventory():
    if 'user' not in session:
        return redirect(url_for('login'))
    logistics = LogisticsSystem(db_manager, cloud_sync, session['user'])
    if request.method == 'POST':
        item_id = request.form['item_id']
        name = request.form['name']
        quantity = int(request.form['quantity'])
        location = request.form['location']
        logistics.add_inventory(item_id, name, quantity, location)
        return redirect(url_for('home'))
    return render_template('add_inventory.html')

@app.route('/schedule_shipment', methods=['GET', 'POST'])
def schedule_shipment():
    if 'user' not in session:
        return redirect(url_for('login'))
    logistics = LogisticsSystem(db_manager, cloud_sync, session['user'])
    if request.method == 'POST':
        shipment_id = f"SHIP-{uuid.uuid4().hex[:8]}"
        item_id = request.form['item_id']
        quantity = int(request.form['quantity'])
        destination = request.form['destination']
        scheduled_date = datetime.datetime.strptime(request.form['scheduled_date'], '%Y-%m-%d')
        logistics.schedule_shipment(shipment_id, item_id, quantity, destination, scheduled_date)
        return redirect(url_for('home'))
    return render_template('schedule_shipment.html')

@app.route('/reset', methods=['GET', 'POST'])
def reset():
    if 'user' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        reset_database(session['user'])
        flash("Inventory and shipments reset successfully.")
        return redirect(url_for('home'))
    return render_template('reset.html')

if __name__ == "__main__":
    app.run(debug=True)