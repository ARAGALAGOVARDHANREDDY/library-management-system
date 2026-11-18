
from getpass import getpass

from passlib.context import CryptContext
from sqlalchemy.orm import Session

import models
from database import SessionLocal


# Password hashing
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)


def create_admin():

    print("\n===== CREATE ADMIN ACCOUNT =====\n")

    email = input("Enter admin email: ").strip().lower()

    password = getpass("Enter admin password: ")
    confirm_password = getpass("Confirm admin password: ")

    if not email or not password:
        print("Email and password are required.")
        return

    if len(password) < 8:
        print("Password must contain at least 8 characters.")
        return

    if len(password.encode("utf-8")) > 72:
        print("Password must not exceed 72 bytes.")
        return

    if password != confirm_password:
        print("Passwords do not match.")
        return

    db: Session = SessionLocal()

    try:

        # Check whether email already exists
        existing_user = (
            db.query(models.User)
            .filter(models.User.email == email)
            .first()
        )

        if existing_user:
            print("An account with this email already exists.")
            print("Use another email or manage the existing account.")
            return

        # Hash password
        hashed_password = pwd_context.hash(password)

        # Create admin account
        admin = models.User(
            email=email,
            password_hash=hashed_password,
            role="admin",
            member_id=None,
            is_active=True
        )

        db.add(admin)
        db.commit()
        db.refresh(admin)

        print("\nAdmin account created successfully!")
        print("Admin ID:", admin.id)
        print("Admin Email:", admin.email)
        print("Role:", admin.role)

    except Exception as error:

        db.rollback()
        print("Error creating admin:", error)

    finally:
        db.close()


if __name__ == "__main__":
    create_admin()
