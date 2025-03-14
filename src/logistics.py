import datetime
import json
import sqlite3
from typing import Dict, List, Optional
from threading import Lock
import logging
import firebase_admin
from firebase_admin import credentials, db, auth

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')

# Fix SQLite datetime deprecation warning
def adapt_datetime(dt):
    return dt.isoformat()

def convert_datetime(s):
    return datetime.datetime.fromisoformat(s.decode('utf-8'))

sqlite3.register_adapter(datetime.datetime, adapt_datetime)
sqlite3.register_converter("TIMESTAMP", convert_datetime)

# Initialize Firebase
try:
    cred = credentials.Certificate("/Users/rohits/Desktop/Inv_mgmt/config/serviceAccountKey.json")
    firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://logisticsdemo-07-default-rtdb.firebaseio.com/'
    })
except Exception as e:
    logging.error(f"Failed to initialize Firebase: {str(e)}")
    raise

class InventoryItem:
    def __init__(self, item_id: str, name: str, quantity: int, location: str):
        self.item_id = item_id
        self.name = name
        self.quantity = quantity
        self.location = location
        self.last_updated = datetime.datetime.now()

class DatabaseManager:
    def __init__(self, db_name: str = "logistics.db"):
        self.db_name = db_name
        self.lock = Lock()
        self._initialize_db()

    def _initialize_db(self):
        with sqlite3.connect(self.db_name, detect_types=sqlite3.PARSE_DECLTYPES) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS inventory (
                    item_id TEXT PRIMARY KEY,
                    name TEXT,
                    quantity INTEGER,
                    location TEXT,
                    last_updated TIMESTAMP
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS shipments (
                    shipment_id TEXT PRIMARY KEY,
                    item_id TEXT,
                    quantity INTEGER,
                    destination TEXT,
                    status TEXT,
                    scheduled_date TIMESTAMP,
                    FOREIGN KEY (item_id) REFERENCES inventory (item_id)
                )
            ''')
            conn.commit()

    def update_inventory(self, item: InventoryItem):
        with self.lock:
            with sqlite3.connect(self.db_name, detect_types=sqlite3.PARSE_DECLTYPES) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO inventory 
                    (item_id, name, quantity, location, last_updated)
                    VALUES (?, ?, ?, ?, ?)
                ''', (item.item_id, item.name, item.quantity, item.location, 
                      item.last_updated))
                conn.commit()

class CloudSync:
    def __init__(self):
        self.ref = db.reference('inventory')

    def sync_inventory(self, items: List[InventoryItem]) -> bool:
        try:
            data = {item.item_id: {
                "name": item.name,
                "quantity": item.quantity,
                "location": item.location,
                "last_updated": item.last_updated.isoformat()
            } for item in items}
            self.ref.update(data)
            logging.info("Firebase sync successful")
            return True
        except Exception as e:
            logging.error(f"Firebase sync failed: {str(e)}")
            return False

class LogisticsSystem:
    def __init__(self, db_manager: DatabaseManager, cloud_sync: CloudSync):
        self.db_manager = db_manager
        self.cloud_sync = cloud_sync
        self.inventory: Dict[str, InventoryItem] = {}
        self.shipments: Dict[str, dict] = {}
        self._load_initial_data()

    def _load_initial_data(self):
        with sqlite3.connect(self.db_manager.db_name, detect_types=sqlite3.PARSE_DECLTYPES) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM inventory")
            for row in cursor.fetchall():
                item = InventoryItem(row[0], row[1], row[2], row[3])
                item.last_updated = row[4]
                self.inventory[item.item_id] = item

            cursor.execute("SELECT * FROM shipments WHERE status = 'PENDING'")
            for row in cursor.fetchall():
                shipment_id, item_id, quantity, destination, status, scheduled_date = row
                self.shipments[shipment_id] = {
                    "item_id": item_id,
                    "quantity": quantity,
                    "destination": destination,
                    "status": status,
                    "scheduled_date": scheduled_date
                }
                if item_id in self.inventory:
                    self.inventory[item_id].quantity -= quantity
                    self.inventory[item_id].last_updated = datetime.datetime.now()
                    self.db_manager.update_inventory(self.inventory[item_id])
                    self.cloud_sync.sync_inventory([self.inventory[item_id]])

    def add_inventory(self, item_id: str, name: str, quantity: int, location: str):
        item = InventoryItem(item_id, name, quantity, location)
        self.inventory[item_id] = item
        self.db_manager.update_inventory(item)
        self.cloud_sync.sync_inventory([item])
        logging.info(f"Added item {item_id} to inventory")

    def update_quantity(self, item_id: str, quantity_change: int):
        if item_id not in self.inventory:
            raise ValueError("Item not found")
        
        item = self.inventory[item_id]
        item.quantity += quantity_change
        item.last_updated = datetime.datetime.now()
        
        if item.quantity < 0:
            raise ValueError("Quantity cannot be negative")
            
        self.db_manager.update_inventory(item)
        self.cloud_sync.sync_inventory([item])
        logging.info(f"Updated quantity for item {item_id}")

    def schedule_shipment(self, shipment_id: str, item_id: str, 
                        quantity: int, destination: str, 
                        scheduled_date: datetime.datetime) -> bool:
        if item_id not in self.inventory:
            raise ValueError("Item not found")
        
        if self.inventory[item_id].quantity < quantity:
            raise ValueError("Insufficient inventory")
            
        with sqlite3.connect(self.db_manager.db_name, detect_types=sqlite3.PARSE_DECLTYPES) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT shipment_id FROM shipments WHERE shipment_id = ?", (shipment_id,))
            if cursor.fetchone():
                logging.info(f"Shipment {shipment_id} already exists, skipping")
                return False
            
            cursor.execute('''
                INSERT INTO shipments 
                (shipment_id, item_id, quantity, destination, status, scheduled_date)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (shipment_id, item_id, quantity, destination, "PENDING", 
                  scheduled_date))
            conn.commit()
            
        self.update_quantity(item_id, -quantity)
        self.shipments[shipment_id] = {
            "item_id": item_id,
            "quantity": quantity,
            "destination": destination,
            "status": "PENDING",
            "scheduled_date": scheduled_date
        }
        logging.info(f"Scheduled shipment {shipment_id}")
        return True

    def get_inventory_status(self) -> Dict[str, dict]:
        return {
            item_id: {
                "name": item.name,
                "quantity": item.quantity,
                "location": item.location,
                "last_updated": item.last_updated.isoformat()
            } for item_id, item in self.inventory.items()
        }

    def get_shipments(self) -> Dict[str, dict]:
        return {
            shipment_id: {
                "item_id": info["item_id"],
                "quantity": info["quantity"],
                "destination": info["destination"],
                "status": info["status"],
                "scheduled_date": info["scheduled_date"].isoformat()  # Convert datetime to string
            } for shipment_id, info in self.shipments.items()
        }