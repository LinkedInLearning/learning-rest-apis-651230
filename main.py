import os
from typing import List, Optional
from datetime import date, datetime, timedelta
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from dotenv import load_dotenv
from sqlalchemy import (
    String,
    Column,
    Integer,
    BigInteger,
    Date,
    DateTime,
    Boolean,
    Numeric,
    ForeignKey,
)
from sqlalchemy.orm import Session, relationship, DeclarativeBase
from sqlalchemy import create_engine

app = FastAPI()


# Pydantic models for API responses
class BookResponse(BaseModel):
    isbn: int
    title: str
    author: str
    publisher: Optional[str] = None
    year: Optional[int] = None
    pages: Optional[int] = None
    genre: Optional[str] = None
    location: Optional[str] = None

    class Config:
        from_attributes = True


class UserResponse(BaseModel):
    userId: int
    name: str
    email: str
    memberSince: date
    checkedOutBooks: List[int]
    fineBalance: float
    address: Optional[str] = None
    phoneNumber: Optional[str] = None

    class Config:
        from_attributes = True


# Pydantic models for API input
class BookIn(BaseModel):
    isbn: int
    title: str
    author: str
    publisher: Optional[str] = None
    year: Optional[int] = None
    pages: Optional[int] = None
    genre: Optional[str] = None
    location: Optional[str] = None


class UserIn(BaseModel):
    name: str
    email: str
    address: Optional[str] = None
    phoneNumber: Optional[str] = None


# Pydantic models for partial updates (PATCH)
class BookUpdate(BaseModel):
    title: Optional[str] = None
    author: Optional[str] = None
    publisher: Optional[str] = None
    year: Optional[int] = None
    pages: Optional[int] = None
    genre: Optional[str] = None
    location: Optional[str] = None


class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    phoneNumber: Optional[str] = None


class CheckoutIn(BaseModel):
    userId: int
    isbn: int


# SqlAlchemy models
class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    member_since = Column(Date, nullable=False, default=date.today)
    fine_balance = Column(Numeric(10, 2), default=0.00)
    address = Column(String(500))
    phone_number = Column(String(20))

    # Relationship
    checkouts = relationship("Checkout", back_populates="user")


class Book(Base):
    __tablename__ = "books"

    isbn = Column(BigInteger, primary_key=True)
    title = Column(String(500), nullable=False)
    author = Column(String(255), nullable=False)
    publisher = Column(String(255))
    year = Column(Integer)
    pages = Column(Integer)
    genre = Column(String(100))
    location = Column(String(100))
    is_available = Column(Boolean, default=True)

    # Relationship
    checkouts = relationship("Checkout", back_populates="book")


class Checkout(Base):
    __tablename__ = "checkouts"

    checkout_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    isbn = Column(BigInteger, ForeignKey("books.isbn"), nullable=False)
    checkout_date = Column(DateTime, default=datetime.now)
    due_date = Column(DateTime, nullable=False)
    return_date = Column(DateTime)

    # Relationships
    user = relationship("User", back_populates="checkouts")
    book = relationship("Book", back_populates="checkouts")


# Connect to the database
load_dotenv(".env")
DBUSER = os.environ["DBUSER"]
DBPASS = os.environ["DBPASS"]
DBHOST = os.environ["DBHOST"]
DBNAME = os.environ["DBNAME"]
DATABASE_URI = f"postgresql://{DBUSER}:{DBPASS}@{DBHOST}/{DBNAME}"

engine = create_engine(DATABASE_URI, echo=False, pool_pre_ping=True)


def wait_for_database(max_retries: int = 30) -> None:
    for attempt in range(max_retries):
        try:
            with engine.connect() as connection:
                connection.close()
            return
        except Exception:
            if attempt == max_retries - 1:
                raise

            wait_time = min(attempt + 1, 5)
            print(
                f"Database not ready (attempt {attempt + 1}/{max_retries}). "
                f"Retrying in {wait_time}s..."
            )
            time.sleep(wait_time)


def initialize_database() -> None:
    wait_for_database()
    Base.metadata.create_all(engine)


@app.on_event("startup")
def on_startup() -> None:
    initialize_database()


@app.get("/")
def root():
    return "Welcome to the Library REST API. Add /docs to the URL to see API methods."


@app.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id: int):
    with Session(engine) as session:
        # Get user
        user = session.query(User).filter(User.user_id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Get checked out books (books that haven't been returned)
        checked_out = (
            session.query(Checkout.isbn)
            .filter(Checkout.user_id == user_id, Checkout.return_date.is_(None))
            .all()
        )

        checked_out_isbns = [checkout.isbn for checkout in checked_out]

        return UserResponse(
            userId=user.user_id,
            name=user.name,
            email=user.email,
            memberSince=user.member_since,
            checkedOutBooks=checked_out_isbns,
            fineBalance=float(user.fine_balance),
            address=user.address,
            phoneNumber=user.phone_number,
        )


@app.get("/books/{isbn}", response_model=BookResponse)
def get_book(isbn: int):
    with Session(engine) as session:
        book = session.query(Book).filter(Book.isbn == isbn).first()
        if not book:
            raise HTTPException(status_code=404, detail="Book not found")

        return BookResponse(
            isbn=book.isbn,
            title=book.title,
            author=book.author,
            publisher=book.publisher,
            year=book.year,
            pages=book.pages,
            genre=book.genre,
            location=book.location,
        )


@app.post("/users")
def create_user(user: UserIn):
    with Session(engine) as session:
        # Check if email already exists
        existing = session.query(User).filter(User.email == user.email).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")

        # Get next user_id (you might want to use autoincrement instead)
        max_id = session.query(User.user_id).order_by(User.user_id.desc()).first()
        next_id = (max_id[0] + 1) if max_id else 100000

        new_user = User(
            user_id=next_id,
            name=user.name,
            email=user.email,
            address=user.address,
            phone_number=user.phoneNumber,
            member_since=date.today(),
        )
        session.add(new_user)
        session.commit()

        return {"message": f"User created with ID {new_user.user_id}"}


@app.post("/books")
def create_book(book: BookIn):
    with Session(engine) as session:
        # Check if ISBN already exists
        existing = session.query(Book).filter(Book.isbn == book.isbn).first()
        if existing:
            raise HTTPException(
                status_code=400, detail="Book with this ISBN already exists"
            )

        new_book = Book(
            isbn=book.isbn,
            title=book.title,
            author=book.author,
            publisher=book.publisher,
            year=book.year,
            pages=book.pages,
            genre=book.genre,
            location=book.location,
        )
        session.add(new_book)
        session.commit()

        return {"message": f"Book '{book.title}' added to library"}


@app.post("/checkout")
def checkout_book(checkout: CheckoutIn):
    with Session(engine) as session:
        # Check if user exists
        user = session.query(User).filter(User.user_id == checkout.userId).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Check if book exists and is available
        book = session.query(Book).filter(Book.isbn == checkout.isbn).first()
        if not book:
            raise HTTPException(status_code=404, detail="Book not found")
        if not book.is_available:
            raise HTTPException(status_code=400, detail="Book is not available")

        # Create checkout record
        due_date = datetime.now().replace(hour=23, minute=59, second=59) + timedelta(
            days=30
        )
        new_checkout = Checkout(
            user_id=checkout.userId, isbn=checkout.isbn, due_date=due_date
        )

        # Mark book as unavailable
        book.is_available = False

        session.add(new_checkout)
        session.commit()

        return {
            "message": f"Book '{book.title}' checked out to {user.name}",
            "dueDate": due_date,
        }


@app.post("/return/{isbn}")
def return_book(isbn: int, user_id: int):
    with Session(engine) as session:
        # Find the checkout record
        checkout = (
            session.query(Checkout)
            .filter(
                Checkout.isbn == isbn,
                Checkout.user_id == user_id,
                Checkout.return_date.is_(None),
            )
            .first()
        )

        if not checkout:
            raise HTTPException(
                status_code=404,
                detail="No active checkout found for this book and user",
            )

        # Mark as returned
        checkout.return_date = datetime.now()

        # Mark book as available
        book = session.query(Book).filter(Book.isbn == isbn).first()
        book.is_available = True

        # Calculate any late fees (optional)
        if checkout.return_date > checkout.due_date:
            days_late = (checkout.return_date - checkout.due_date).days
            late_fee = days_late * 0.50  # 50 cents per day
            user = session.query(User).filter(User.user_id == user_id).first()
            user.fine_balance += late_fee

            session.commit()
            return {"message": f"Book returned. Late fee of ${late_fee:.2f} applied."}

        session.commit()
        return {"message": "Book returned successfully"}


@app.get("/users")
def get_all_users():
    with Session(engine) as session:
        users = session.query(User).all()
        return [{"userId": u.user_id, "name": u.name, "email": u.email} for u in users]


@app.get("/books")
def get_all_books():
    with Session(engine) as session:
        books = session.query(Book).all()
        return [
            {
                "isbn": b.isbn,
                "title": b.title,
                "author": b.author,
                "available": b.is_available,
            }
            for b in books
        ]


# PUT methods - Full resource updates
@app.put("/users/{user_id}")
def update_user(user_id: int, user: UserIn):
    with Session(engine) as session:
        existing_user = session.query(User).filter(User.user_id == user_id).first()
        if not existing_user:
            raise HTTPException(status_code=404, detail="User not found")

        # Check if email is being changed and if new email already exists
        if user.email != existing_user.email:
            email_exists = session.query(User).filter(User.email == user.email).first()
            if email_exists:
                raise HTTPException(status_code=400, detail="Email already registered")

        # Update all fields
        existing_user.name = user.name
        existing_user.email = user.email
        existing_user.address = user.address
        existing_user.phone_number = user.phoneNumber

        session.commit()
        return {"message": f"User {user_id} updated successfully"}


@app.put("/books/{isbn}")
def update_book(isbn: int, book: BookIn):
    with Session(engine) as session:
        existing_book = session.query(Book).filter(Book.isbn == isbn).first()
        if not existing_book:
            raise HTTPException(status_code=404, detail="Book not found")

        # Check if ISBN is being changed and if new ISBN already exists
        if book.isbn != isbn:
            isbn_exists = session.query(Book).filter(Book.isbn == book.isbn).first()
            if isbn_exists:
                raise HTTPException(
                    status_code=400, detail="Book with this ISBN already exists"
                )
            existing_book.isbn = book.isbn

        # Update all fields
        existing_book.title = book.title
        existing_book.author = book.author
        existing_book.publisher = book.publisher
        existing_book.year = book.year
        existing_book.pages = book.pages
        existing_book.genre = book.genre
        existing_book.location = book.location

        session.commit()
        return {"message": f"Book '{book.title}' updated successfully"}


# PATCH methods - Partial resource updates
@app.patch("/users/{user_id}")
def patch_user(user_id: int, user_update: UserUpdate):
    with Session(engine) as session:
        existing_user = session.query(User).filter(User.user_id == user_id).first()
        if not existing_user:
            raise HTTPException(status_code=404, detail="User not found")

        # Check if email is being changed and if new email already exists
        if user_update.email and user_update.email != existing_user.email:
            email_exists = (
                session.query(User).filter(User.email == user_update.email).first()
            )
            if email_exists:
                raise HTTPException(status_code=400, detail="Email already registered")

        # Update only provided fields
        if user_update.name is not None:
            existing_user.name = user_update.name
        if user_update.email is not None:
            existing_user.email = user_update.email
        if user_update.address is not None:
            existing_user.address = user_update.address
        if user_update.phoneNumber is not None:
            existing_user.phone_number = user_update.phoneNumber

        session.commit()
        return {"message": f"User {user_id} updated successfully"}


@app.patch("/books/{isbn}")
def patch_book(isbn: int, book_update: BookUpdate):
    with Session(engine) as session:
        existing_book = session.query(Book).filter(Book.isbn == isbn).first()
        if not existing_book:
            raise HTTPException(status_code=404, detail="Book not found")

        # Update only provided fields
        if book_update.title is not None:
            existing_book.title = book_update.title
        if book_update.author is not None:
            existing_book.author = book_update.author
        if book_update.publisher is not None:
            existing_book.publisher = book_update.publisher
        if book_update.year is not None:
            existing_book.year = book_update.year
        if book_update.pages is not None:
            existing_book.pages = book_update.pages
        if book_update.genre is not None:
            existing_book.genre = book_update.genre
        if book_update.location is not None:
            existing_book.location = book_update.location

        session.commit()
        return {"message": f"Book '{existing_book.title}' updated successfully"}


# DELETE methods
@app.delete("/users/{user_id}")
def delete_user(user_id: int):
    with Session(engine) as session:
        user = session.query(User).filter(User.user_id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Check if user has active checkouts
        active_checkouts = (
            session.query(Checkout)
            .filter(Checkout.user_id == user_id, Checkout.return_date.is_(None))
            .count()
        )

        if active_checkouts > 0:
            raise HTTPException(
                status_code=400,
                detail="Cannot delete user with active book checkouts. Please return all books first.",
            )

        # Delete the user (this will cascade to checkout history if needed)
        session.delete(user)
        session.commit()
        return {"message": f"User {user_id} deleted successfully"}


@app.delete("/books/{isbn}")
def delete_book(isbn: int):
    with Session(engine) as session:
        book = session.query(Book).filter(Book.isbn == isbn).first()
        if not book:
            raise HTTPException(status_code=404, detail="Book not found")

        # Check if book is currently checked out
        if not book.is_available:
            raise HTTPException(
                status_code=400,
                detail="Cannot delete book that is currently checked out",
            )

        # Delete the book (this will cascade to checkout history if needed)
        session.delete(book)
        session.commit()
        return {"message": f"Book '{book.title}' deleted successfully"}
