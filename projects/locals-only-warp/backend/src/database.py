"""
Database handler for DuckDB integration.
Manages user data storage and retrieval.
"""
import json
import logging
import uuid
from pathlib import Path
from typing import List, Optional, Dict, Any
from contextlib import asynccontextmanager

import duckdb

from .config import get_settings

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Database manager for DuckDB operations."""
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize database manager.
        
        Args:
            db_path: Path to the DuckDB database file. If None, uses in-memory database.
        """
        self.settings = get_settings()
        
        # Use persistent database file in development, in-memory for tests
        if db_path is None:
            if self.settings.debug:
                # Create data directory if it doesn't exist
                data_dir = Path("data")
                data_dir.mkdir(exist_ok=True)
                self.db_path = str(data_dir / "app.duckdb")
            else:
                self.db_path = ":memory:"  # In-memory for production/tests
        else:
            self.db_path = db_path
        
        self._connection = None
        self._initialize_database()
    
    def _get_connection(self) -> duckdb.DuckDBPyConnection:
        """Get database connection, creating one if needed."""
        if self._connection is None:
            self._connection = duckdb.connect(self.db_path)
        return self._connection
    
    def _initialize_database(self):
        """Initialize database schema."""
        conn = self._get_connection()
        
        # Create users table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id VARCHAR PRIMARY KEY,
                phone_number VARCHAR UNIQUE NOT NULL,
                starred_categories JSON DEFAULT '[]',
                cached_recommendations JSON DEFAULT '[]',
                bookmarks JSON DEFAULT '[]',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Note: DuckDB doesn't support triggers, so we handle updated_at manually in update methods
        
        conn.commit()
        logger.info(f"Database initialized with path: {self.db_path}")
    
    def close(self):
        """Close database connection."""
        if self._connection:
            self._connection.close()
            self._connection = None
    
    # User CRUD operations
    
    def create_user(self, phone_number: str, starred_categories: List[str] = None) -> Dict[str, Any]:
        """Create a new user.
        
        Args:
            phone_number: User's phone number
            starred_categories: List of starred categories
            
        Returns:
            Dict containing the created user data
            
        Raises:
            ValueError: If phone number already exists
        """
        if starred_categories is None:
            starred_categories = []
            
        user_id = str(uuid.uuid4())
        conn = self._get_connection()
        
        try:
            conn.execute("""
                INSERT INTO users (id, phone_number, starred_categories, cached_recommendations, bookmarks)
                VALUES (?, ?, ?, ?, ?)
            """, (
                user_id,
                phone_number,
                json.dumps(starred_categories),
                json.dumps([]),
                json.dumps([])
            ))
            conn.commit()
            
            logger.info(f"Created user with ID: {user_id}")
            return self.get_user(user_id)
            
        except duckdb.IntegrityError as e:
            if "UNIQUE constraint failed" in str(e):
                raise ValueError(f"Phone number {phone_number} already exists")
            raise
    
    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID.
        
        Args:
            user_id: User's unique ID
            
        Returns:
            Dict containing user data or None if not found
        """
        conn = self._get_connection()
        
        result = conn.execute("""
            SELECT id, phone_number, starred_categories, cached_recommendations, bookmarks,
                   created_at, updated_at
            FROM users 
            WHERE id = ?
        """, (user_id,)).fetchone()
        
        if result:
            return {
                'id': result[0],
                'phone_number': result[1],
                'starred_categories': json.loads(result[2]) if result[2] else [],
                'cached_recommendations': json.loads(result[3]) if result[3] else [],
                'bookmarks': json.loads(result[4]) if result[4] else [],
                'created_at': result[5],
                'updated_at': result[6]
            }
        return None
    
    def get_user_by_phone(self, phone_number: str) -> Optional[Dict[str, Any]]:
        """Get user by phone number.
        
        Args:
            phone_number: User's phone number
            
        Returns:
            Dict containing user data or None if not found
        """
        conn = self._get_connection()
        
        result = conn.execute("""
            SELECT id, phone_number, starred_categories, cached_recommendations, bookmarks,
                   created_at, updated_at
            FROM users 
            WHERE phone_number = ?
        """, (phone_number,)).fetchone()
        
        if result:
            return {
                'id': result[0],
                'phone_number': result[1],
                'starred_categories': json.loads(result[2]) if result[2] else [],
                'cached_recommendations': json.loads(result[3]) if result[3] else [],
                'bookmarks': json.loads(result[4]) if result[4] else [],
                'created_at': result[5],
                'updated_at': result[6]
            }
        return None
    
    def update_user(self, user_id: str, **updates) -> Optional[Dict[str, Any]]:
        """Update user data.
        
        Args:
            user_id: User's unique ID
            **updates: Fields to update (phone_number, starred_categories, 
                      cached_recommendations, bookmarks)
            
        Returns:
            Dict containing updated user data or None if user not found
        """
        conn = self._get_connection()
        
        # Check if user exists
        if not self.get_user(user_id):
            return None
        
        # Build dynamic update query
        update_fields = []
        update_values = []
        
        if 'phone_number' in updates:
            update_fields.append("phone_number = ?")
            update_values.append(updates['phone_number'])
        
        if 'starred_categories' in updates:
            update_fields.append("starred_categories = ?")
            update_values.append(json.dumps(updates['starred_categories']))
        
        if 'cached_recommendations' in updates:
            update_fields.append("cached_recommendations = ?")
            update_values.append(json.dumps(updates['cached_recommendations']))
        
        if 'bookmarks' in updates:
            update_fields.append("bookmarks = ?")
            update_values.append(json.dumps(updates['bookmarks']))
        
        if not update_fields:
            return self.get_user(user_id)  # No updates, return current data
        
        # Always update the updated_at field
        update_fields.append("updated_at = CURRENT_TIMESTAMP")
        update_values.append(user_id)
        
        query = f"UPDATE users SET {', '.join(update_fields)} WHERE id = ?"
        
        try:
            conn.execute(query, update_values)
            conn.commit()
            
            logger.info(f"Updated user with ID: {user_id}")
            return self.get_user(user_id)
            
        except duckdb.IntegrityError as e:
            if "UNIQUE constraint failed" in str(e):
                raise ValueError(f"Phone number {updates.get('phone_number')} already exists")
            raise
    
    def delete_user(self, user_id: str) -> bool:
        """Delete user by ID.
        
        Args:
            user_id: User's unique ID
            
        Returns:
            True if user was deleted, False if user not found
        """
        conn = self._get_connection()
        
        result = conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        
        deleted = result.rowcount > 0
        if deleted:
            logger.info(f"Deleted user with ID: {user_id}")
        
        return deleted
    
    def list_users(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """List all users with pagination.
        
        Args:
            limit: Maximum number of users to return
            offset: Number of users to skip
            
        Returns:
            List of user dictionaries
        """
        conn = self._get_connection()
        
        results = conn.execute("""
            SELECT id, phone_number, starred_categories, cached_recommendations, bookmarks,
                   created_at, updated_at
            FROM users 
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        """, (limit, offset)).fetchall()
        
        users = []
        for result in results:
            users.append({
                'id': result[0],
                'phone_number': result[1],
                'starred_categories': json.loads(result[2]) if result[2] else [],
                'cached_recommendations': json.loads(result[3]) if result[3] else [],
                'bookmarks': json.loads(result[4]) if result[4] else [],
                'created_at': result[5],
                'updated_at': result[6]
            })
        
        return users
    
    def count_users(self) -> int:
        """Count total number of users.
        
        Returns:
            Total number of users
        """
        conn = self._get_connection()
        result = conn.execute("SELECT COUNT(*) FROM users").fetchone()
        return result[0] if result else 0


# Global database instance
_db_manager: Optional[DatabaseManager] = None


def get_db_manager() -> DatabaseManager:
    """Get the global database manager instance."""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager


@asynccontextmanager
async def get_db():
    """Async context manager for database operations."""
    db = get_db_manager()
    try:
        yield db
    finally:
        # Database connection is managed by the DatabaseManager
        pass


def close_db():
    """Close the global database connection."""
    global _db_manager
    if _db_manager:
        _db_manager.close()
        _db_manager = None
