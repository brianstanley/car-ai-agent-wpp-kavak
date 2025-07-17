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

