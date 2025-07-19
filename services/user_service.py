#!/usr/bin/env python3
"""
User management service.
"""

import psycopg2
from typing import Optional

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from db.config import Config
from db.session import SessionLocal
from models.db import UserDB
from models.schemas.user import User


class UserService:
    def __init__(self):
        self.connection_string = Config.DATABASE_URL

    # Convert userDb to Pydantic schema
    def _to_schema(self, db_user: UserDB) -> User:
        return User(
            id=db_user.id,
            phone_number=db_user.phone_number,
            name=db_user.name,
            preferences=db_user.preferences,
            created_at=db_user.created_at
        )

    def get_connection(self):
        return psycopg2.connect(self.connection_string)

    def get_or_create_user(self, phone_number: str) -> User:
        with SessionLocal() as session:
            user = session.scalar(select(UserDB).where(UserDB.phone_number == phone_number))
            if user:
                return self._to_schema(user)

            new_user = UserDB(phone_number=phone_number)
            session.add(new_user)
            session.commit()
            session.refresh(new_user)
            return self._to_schema(new_user)

    #update user name
    def update_user_name(self, id: str, name: str) -> Optional[User]:
        try:
            with SessionLocal() as session:
                db_user = session.scalar(select(UserDB).where(UserDB.id == id))
                if not db_user:
                    print(f"❌ User not found with id: {id}")
                    return None

                print(f"DEBUG: Updating user name for user {id}")
                print(f"DEBUG: Current name: {db_user.name}")
                print(f"📝DEBUG: New name to set: {name}")

                db_user.name = name
                session.commit()
                session.refresh(db_user)

                print(f"DEBUG: User name updated successfully")
                print(f"DEBUG: Final name: {db_user.name}")

                return self._to_schema(db_user)
        except SQLAlchemyError as e:
            print(f"❌ Error al actualizar el nombre del usuario: {e}")
            raise

    def update_preferences(self, id: str, preferences: dict) -> Optional[User]:
        try:
            with SessionLocal() as session:
                db_user = session.scalar(select(UserDB).where(UserDB.id == id))
                if not db_user:
                    print(f"❌ User not found with id: {id}")
                    return None

                print(f"DEBUG: Updating preferences for user {id}")
                print(f"DEBUG: Current preferences: {db_user.preferences}")
                print(f"📝DEBUG: New preferences to add: {preferences}")

                current = db_user.preferences or {}
                if not isinstance(current, dict):
                    current = {}
                current.update(preferences)
                print(f"DEBUG: Merged preferences: {current}")
                db_user.preferences = current
                # workaround for sqlalchemy not detecting changes in dict
                from sqlalchemy.orm.attributes import flag_modified
                flag_modified(db_user, "preferences")

                session.commit()
                session.refresh(db_user)

                print(f"DEBUG: Preferences updated successfully")
                print(f"DEBUG: Final preferences: {db_user.preferences}")

                return self._to_schema(db_user)
        except SQLAlchemyError as e:
            print(f"❌ Error al actualizar preferencias: {e}")
            raise

    def get_user_by_phone(self, phone_number: str) -> Optional[User]:
        try:
            with SessionLocal() as session:
                db_user = session.scalar(select(UserDB).where(UserDB.phone_number == phone_number))
                return self._to_schema(db_user) if db_user else None
        except SQLAlchemyError as e:
            print(f"❌ Error in get_user_by_phone: {e}")
            raise

    def get_all_users(self) -> list[User]:
        """Get all users from the database."""
        try:
            with SessionLocal() as session:
                db_users = session.scalars(select(UserDB)).all()
                return [self._to_schema(user) for user in db_users]
        except SQLAlchemyError as e:
            print(f"❌ Error in get_all_users: {e}")
            raise

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get a user by their ID."""
        try:
            from uuid import UUID
            with SessionLocal() as session:
                db_user = session.scalar(select(UserDB).where(UserDB.id == UUID(user_id)))
                return self._to_schema(db_user) if db_user else None
        except SQLAlchemyError as e:
            print(f"❌ Error in get_user_by_id: {e}")
            raise
        except ValueError as e:
            print(f"❌ Invalid UUID format: {e}")
            raise

    def update_user(self, user_id: str, name: Optional[str] = None, preferences: Optional[dict] = None) -> Optional[User]:
        """Update a user's name and/or preferences."""
        try:
            from uuid import UUID
            with SessionLocal() as session:
                db_user = session.scalar(select(UserDB).where(UserDB.id == UUID(user_id)))
                if not db_user:
                    print(f"❌ User not found with id: {user_id}")
                    return None

                print(f"DEBUG: Updating user {user_id}")
                
                # Update name if provided
                if name is not None:
                    print(f"DEBUG: Updating name from '{db_user.name}' to '{name}'")
                    db_user.name = name

                # Update preferences if provided
                if preferences is not None:
                    print(f"DEBUG: Updating preferences from {db_user.preferences} to {preferences}")
                    current = db_user.preferences or {}
                    if not isinstance(current, dict):
                        current = {}
                    current.update(preferences)
                    db_user.preferences = current
                    # Workaround for sqlalchemy not detecting changes in dict
                    from sqlalchemy.orm.attributes import flag_modified
                    flag_modified(db_user, "preferences")

                session.commit()
                session.refresh(db_user)

                print(f"DEBUG: User updated successfully")
                return self._to_schema(db_user)
        except SQLAlchemyError as e:
            print(f"❌ Error updating user: {e}")
            raise
        except ValueError as e:
            print(f"❌ Invalid UUID format: {e}")
            raise

    def delete_user(self, user_id: str) -> bool:
        """Delete a user by their ID."""
        try:
            from uuid import UUID
            with SessionLocal() as session:
                db_user = session.scalar(select(UserDB).where(UserDB.id == UUID(user_id)))
                if not db_user:
                    print(f"❌ User not found with id: {user_id}")
                    return False

                print(f"DEBUG: Deleting user {user_id}")
                session.delete(db_user)
                session.commit()

                print(f"DEBUG: User deleted successfully")
                return True
        except SQLAlchemyError as e:
            print(f"❌ Error deleting user: {e}")
            raise
        except ValueError as e:
            print(f"❌ Invalid UUID format: {e}")
            raise

