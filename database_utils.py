import sqlite3

def get_connection():
    # Connect to the SQLite database (this creates the file if it doesn't exist)
    conn = sqlite3.connect('driveelite.db', check_same_thread=False)
    conn.row_factory = sqlite3.Row
    
    # 1. Users Table (Renters, Affiliates, Admins)
    conn.execute('''CREATE TABLE IF NOT EXISTS users
                    (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT, role TEXT, full_name TEXT, age INTEGER, contact_number TEXT, address TEXT, id_img TEXT, license_img TEXT, admin_status TEXT)''')
                    
    # 2. Vehicles Table
    conn.execute('''CREATE TABLE IF NOT EXISTS vehicles
                    (id INTEGER PRIMARY KEY AUTOINCREMENT, owner_username TEXT, make TEXT, model TEXT, year TEXT, plate TEXT, bank_name TEXT, account_no TEXT, vehicle_img TEXT, or_cr_img TEXT, category TEXT, approved_price REAL, admin_status TEXT DEFAULT 'PENDING', booking_status TEXT DEFAULT 'AVAILABLE')''')
                    
    # 3. Bookings/Trips Table
    conn.execute('''CREATE TABLE IF NOT EXISTS bookings
                    (id INTEGER PRIMARY KEY AUTOINCREMENT, vehicle_id INTEGER, renter_username TEXT, amount REAL, pickup_loc TEXT, return_loc TEXT, destination TEXT, pickup_time TEXT, return_time TEXT, drive_type TEXT, payment_method TEXT, status TEXT, payout_status TEXT DEFAULT 'PENDING')''')

    # 4. Drivers Table (For Affiliates registering drivers)
    conn.execute('''CREATE TABLE IF NOT EXISTS drivers
                    (id INTEGER PRIMARY KEY AUTOINCREMENT, owner_username TEXT, first_name TEXT, middle_name TEXT, last_name TEXT, birthdate TEXT, age INTEGER, address TEXT, contact_number TEXT, is_owner INTEGER, license_img TEXT, govt_id_img TEXT, admin_status TEXT DEFAULT 'PENDING')''')

    # 5. Vehicle Categories Table (For dynamic pricing)
    conn.execute('''CREATE TABLE IF NOT EXISTS vehicle_categories 
                    (name TEXT PRIMARY KEY, default_price REAL)''')

    # 6. Reviews Table (THIS IS THE ONE THAT WAS MISSING!)
    conn.execute('''CREATE TABLE IF NOT EXISTS reviews
                    (id INTEGER PRIMARY KEY AUTOINCREMENT, booking_id INTEGER, vehicle_id INTEGER, renter_username TEXT, rating INTEGER, review_text TEXT)''')
    
    conn.commit()
    return conn
if __name__ == "__main__":
    init_db()
