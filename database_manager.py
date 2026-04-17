import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

class DatabaseManager:
    def __init__(self):
        self.host = os.getenv("DB_HOST", "localhost")
        self.dbname = os.getenv("DB_NAME", "postgres")
        self.user = os.getenv("DB_USER", "postgres")
        self.password = os.getenv("DB_PASS", "root")
        self.port = os.getenv("DB_PORT", "5432")
        self.conn = None
        
    def get_connection(self):
        """Establish a connection to the PostgreSQL database."""
        try:
            if self.conn is None or self.conn.closed:
                self.conn = psycopg2.connect(
                    host=self.host,
                    database=self.dbname,
                    user=self.user,
                    password=self.password,
                    port=self.port
                )
                self.conn.autocommit = True
            return self.conn
        except Exception as e:
            print(f"❌ Database connection error: {e}")
            return None

    def initialize_database(self):
        """Create tables if they don't exist and seed initial data."""
        conn = self.get_connection()
        if not conn: return
        
        with conn.cursor() as cur:
            # Create Leads table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS leads (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    phone VARCHAR(20),
                    name VARCHAR(100),
                    project_interest TEXT,
                    raw_text TEXT
                );
            """)
            
            # Create Properties table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS properties (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) UNIQUE NOT NULL,
                    location VARCHAR(255),
                    price VARCHAR(100),
                    description TEXT
                );
            """)
            
            # Seed initial property data
            initial_properties = [
                ("SAMANA Hills South 2", "Arjan", "AED 570,000", "Private pools in every unit."),
                ("SAMANA Barari Heights", "Majan", "AED 970,000", "Nature-inspired luxury living."),
                ("SAMANA Palm Vista", "Dubai Islands", "AED 670,000", "Stunning waterfront views."),
                ("SAMANA Creek Horizon", "Dubai Creek", "AED 370,000", "Incredible entry point for investors."),
                ("SAMANA Sky Views", "Arjan", "AED 680,000", "Iconic architecture that stands out."),
                ("SAMANA Golf Avenue", "Studio City", "AED 650,000", "Perfect for a resort-style lifestyle."),
                ("SAMANA Golf Views", "Sports City", "AED 720,000", "Overlooks world-class golf courses."),
                ("SAMANA Greens", "Arjan", "AED 550,000", "Sustainable, eco-friendly community.")
            ]
            
            for name, loc, price, desc in initial_properties:
                cur.execute("""
                    INSERT INTO properties (name, location, price, description)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (name) DO NOTHING;
                """, (name, loc, price, desc))
                
        print("✅ Database initialized and seeded with SAMANA properties.")

    def add_lead(self, phone, name=None, project=None, raw_text=None):
        """Save a new customer lead to the database."""
        conn = self.get_connection()
        if not conn: return False
        
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO leads (phone, name, project_interest, raw_text)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id;
                """, (phone, name, project, raw_text))
                lead_id = cur.fetchone()[0]
                print(f"📍 Lead Saved to Database: ID {lead_id} | Phone {phone}")
                return True
        except Exception as e:
            print(f"⚠️  Error saving lead: {e}")
            return False

    def get_all_properties(self):
        """Fetch all property listings."""
        conn = self.get_connection()
        if not conn: return []
        
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT * FROM properties;")
                return cur.fetchall()
        except Exception as e:
            print(f"⚠️  Error fetching properties: {e}")
            return []

if __name__ == "__main__":
    # Test initialization
    db = DatabaseManager()
    db.initialize_database()
    print("Database testing complete.")
