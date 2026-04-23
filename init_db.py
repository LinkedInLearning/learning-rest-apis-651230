import os
import time
from datetime import date, datetime, timedelta
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

# Load environment variables BEFORE importing main.py
load_dotenv(".env")
DBUSER = os.environ["DBUSER"]
DBPASS = os.environ["DBPASS"]
DBHOST = os.environ["DBHOST"]
DBNAME = os.environ["DBNAME"]
DATABASE_URI = f"postgresql://{DBUSER}:{DBPASS}@{DBHOST}/{DBNAME}"
# Note: SSL not required for docker-compose internal connections

# Create engine with connection retry logic BEFORE importing main.py
max_retries = 30
engine = None
for attempt in range(max_retries):
    try:
        engine = create_engine(DATABASE_URI, echo=True, pool_pre_ping=True)
        # Test the connection
        with engine.connect() as conn:
            conn.close()
        print(f"Database connection successful on attempt {attempt + 1}")
        break
    except Exception as e:
        if attempt < max_retries - 1:
            wait_time = min(2 ** attempt, 10)  # Exponential backoff, max 10 seconds
            print(f"Database not ready (attempt {attempt + 1}/{max_retries}). Retrying in {wait_time}s...")
            time.sleep(wait_time)
        else:
            print(f"Failed to connect to database after {max_retries} attempts: {e}")
            raise

# Now import main.py which will use the engine that's already connected
from main import Base, User, Book, Checkout

def init_database():
    """Initialize the database with sample data"""
    
    # Tables should already be created by main.py on import
    # Just verify the connection works
    try:
        with engine.connect() as conn:
            conn.close()
    except Exception as e:
        print(f"Database connection error: {e}")
        raise
    
    with Session(engine) as session:
        # Check if data already exists
        existing_users = session.query(User).count()
        if existing_users > 0:
            print("Database already contains data. Skipping initialization.")
            return
        
        print("Initializing database with sample data...")
        
        # Create sample users
        users = [
            User(
                user_id=987654,
                name="Nathan Cayden",
                email="nathan@example.com",
                member_since=date(2006, 4, 15),
                fine_balance=0.00,
                address="5432 Street",
                phone_number="5555555555"
            ),
            User(
                user_id=123456,
                name="Austin Finnagan",
                email="austin@example.com",
                member_since=date(2010, 8, 22),
                fine_balance=2.50,
                address="1234 Avenue",
                phone_number="5551234567"
            ),
            User(
                user_id=555555,
                name="Jeharya Vallerija",
                email="jeharya@example.com",
                member_since=date(2015, 1, 10),
                fine_balance=0.00,
                address="9876 Boulevard",
                phone_number="5559876543"
            ),
            User(
                user_id=111111,
                name="Madisyn Roope",
                email="madisyn@example.com",
                member_since=date(2020, 3, 5),
                fine_balance=0.00,
                address="777 Park Lane",
                phone_number="5557778888"
            )
        ]
        
        # Create sample books
        books = [
            Book(
                isbn=9780743273565,
                title="The Great Gatsby",
                author="F. Scott Fitzgerald",
                publisher="Scribner",
                year=1925,
                pages=180,
                genre="Fiction",
                location="3rd Floor, A-12",
                is_available=False  # Checked out by Morten
            ),
            Book(
                isbn=9780452284234,
                title="To Kill a Mockingbird",
                author="Harper Lee",
                publisher="Harper Perennial",
                year=1960,
                pages=324,
                genre="Fiction",
                location="3rd Floor, B-7",
                is_available=False  # Checked out by Morten
            ),
            Book(
                isbn=9780061120084,
                title="Brave New World",
                author="Aldous Huxley",
                publisher="Harper Perennial",
                year=1932,
                pages=288,
                genre="Science Fiction",
                location="2nd Floor, C-3",
                is_available=False  # Checked out by Morten
            ),
            Book(
                isbn=9780140449136,
                title="The Odyssey",
                author="Homer",
                publisher="Penguin Classics",
                year=-800,
                pages=541,
                genre="Epic Poetry",
                location="4th Floor, D-1",
                is_available=True
            ),
            Book(
                isbn=9780553213119,
                title="Moby Dick",
                author="Herman Melville",
                publisher="Bantam Classics",
                year=1851,
                pages=720,
                genre="Fiction",
                location="3rd Floor, A-15",
                is_available=True
            ),
            Book(
                isbn=9780316769174,
                title="The Catcher in the Rye",
                author="J.D. Salinger",
                publisher="Little, Brown and Company",
                year=1951,
                pages=214,
                genre="Fiction",
                location="3rd Floor, B-3",
                is_available=False  # Checked out by Jane
            ),
            Book(
                isbn=9780451524935,
                title="1984",
                author="George Orwell",
                publisher="Signet Classic",
                year=1949,
                pages=328,
                genre="Dystopian Fiction",
                location="2nd Floor, D-8",
                is_available=True
            ),
            Book(
                isbn=9780142437247,
                title="Don Quixote",
                author="Miguel de Cervantes",
                publisher="Penguin Classics",
                year=1605,
                pages=1072,
                genre="Fiction",
                location="4th Floor, A-1",
                is_available=True
            )
        ]
        
        # Add users and books to session
        session.add_all(users)
        session.add_all(books)
        session.commit()
        
        # Create sample checkouts
        now = datetime.now()
        checkouts = [
            # Morten's checkouts (matching your example)
            Checkout(
                user_id=987654,
                isbn=9780743273565,
                checkout_date=now - timedelta(days=11),
                due_date=now + timedelta(days=19)
            ),
            Checkout(
                user_id=987654,
                isbn=9780452284234,
                checkout_date=now - timedelta(days=6),
                due_date=now + timedelta(days=24)
            ),
            Checkout(
                user_id=987654,
                isbn=9780061120084,
                checkout_date=now - timedelta(days=4),
                due_date=now + timedelta(days=26)
            ),
            # Jane has one book checked out
            Checkout(
                user_id=123456,
                isbn=9780316769174,
                checkout_date=now - timedelta(days=20),
                due_date=now - timedelta(days=5)  # Overdue!
            ),
            # Bob returned a book (historical record)
            Checkout(
                user_id=555555,
                isbn=9780451524935,
                checkout_date=now - timedelta(days=40),
                due_date=now - timedelta(days=10),
                return_date=now - timedelta(days=12)  # Returned on time
            )
        ]
        
        session.add_all(checkouts)
        session.commit()
        
        print("Database initialized successfully!")
        print(f"Added {len(users)} users")
        print(f"Added {len(books)} books")
        print(f"Added {len(checkouts)} checkout records")


if __name__ == "__main__":
    init_database()