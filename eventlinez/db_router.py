"""
Database router to handle fallback to SQLite
"""
import logging
import os
from django.conf import settings

logger = logging.getLogger(__name__)

class FallbackRouter:
    """
    A router that attempts to use PostgreSQL first and falls back to SQLite if needed.
    """

    def db_for_read(self, model, **hints):
        try:
            # Try to use the default database (PostgreSQL)
            from django.db import connections
            connections['default'].ensure_connection()
            return 'default'
        except Exception as e:
            # If PostgreSQL is not available, use SQLite
            logger.warning(f"PostgreSQL connection failed: {e}. Using SQLite for read.")
            return 'sqlite'

    def db_for_write(self, model, **hints):
        try:
            # Try to use the default database (PostgreSQL)
            from django.db import connections
            connections['default'].ensure_connection()
            return 'default'
        except Exception as e:
            # If PostgreSQL is not available, use SQLite
            logger.warning(f"PostgreSQL connection failed: {e}. Using SQLite for write.")
            return 'sqlite'

    def allow_relation(self, obj1, obj2, **hints):
        # Allow relations between objects in the same database
        return True

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        # Allow migrations on both databases
        return True
