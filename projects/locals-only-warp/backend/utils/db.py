#!/usr/bin/env python3
"""
Database utility script for DuckDB operations.
Provides command-line interface for database management and queries.

Example usage:
  python db.py --init                           # Initialize database schema
  python db.py --count                          # Count all users
  python db.py --list                           # List all users  
  python db.py --create-user +1234567890        # Create a user with phone number
  python db.py --get-user <user_id>             # Get user by ID
  python db.py --get-by-phone +1234567890       # Get user by phone number
  python db.py --delete-user <user_id>          # Delete user by ID
  python db.py --query "SELECT * FROM users"    # Execute custom SQL query
"""
import argparse
import json
import sys
from pathlib import Path
from typing import Optional, List

# Add parent directory to Python path to access src module
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database import DatabaseManager


def init_database(db_path: Optional[str] = None):
    """Initialize database with schema."""
    print("🗄️  Initializing database...")
    
    try:
        db = DatabaseManager(db_path)
        print(f"✅ Database initialized successfully at: {db.db_path}")
        print(f"📊 Current user count: {db.count_users()}")
        db.close()
        
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        sys.exit(1)


def count_users(db_path: Optional[str] = None):
    """Count total users in database."""
    try:
        db = DatabaseManager(db_path)
        count = db.count_users()
        print(f"📊 Total users in database: {count}")
        db.close()
        
    except Exception as e:
        print(f"❌ Error counting users: {e}")
        sys.exit(1)


def list_users(db_path: Optional[str] = None, limit: int = 10, offset: int = 0, json_output: bool = False):
    """List users with pagination."""
    try:
        db = DatabaseManager(db_path)
        users = db.list_users(limit=limit, offset=offset)
        total = db.count_users()
        
        if json_output:
            print(json.dumps({
                "users": users,
                "total": total,
                "limit": limit,
                "offset": offset
            }, indent=2, default=str))
        else:
            print(f"👥 Users (showing {len(users)} of {total}, offset: {offset}):")
            print("-" * 80)
            
            if not users:
                print("No users found.")
            else:
                for user in users:
                    print(f"ID: {user['id']}")
                    print(f"Phone: {user['phone_number']}")
                    print(f"Starred Categories: {', '.join(user['starred_categories']) if user['starred_categories'] else 'None'}")
                    print(f"Bookmarks: {len(user['bookmarks'])} items")
                    print(f"Cached Recommendations: {len(user['cached_recommendations'])} items")
                    print(f"Created: {user['created_at']}")
                    print(f"Updated: {user['updated_at']}")
                    print("-" * 80)
        
        db.close()
        
    except Exception as e:
        print(f"❌ Error listing users: {e}")
        sys.exit(1)


def create_user(phone_number: str, starred_categories: List[str] = None, db_path: Optional[str] = None):
    """Create a new user."""
    try:
        db = DatabaseManager(db_path)
        user_data = db.create_user(
            phone_number=phone_number,
            starred_categories=starred_categories or []
        )
        
        print("✅ User created successfully!")
        print(f"ID: {user_data['id']}")
        print(f"Phone: {user_data['phone_number']}")
        print(f"Starred Categories: {', '.join(user_data['starred_categories']) if user_data['starred_categories'] else 'None'}")
        print(f"Created: {user_data['created_at']}")
        
        db.close()
        
    except ValueError as e:
        print(f"❌ User creation failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error creating user: {e}")
        sys.exit(1)


def get_user(user_id: str, db_path: Optional[str] = None, json_output: bool = False):
    """Get user by ID."""
    try:
        db = DatabaseManager(db_path)
        user_data = db.get_user(user_id)
        
        if not user_data:
            print(f"❌ User with ID {user_id} not found.")
            sys.exit(1)
        
        if json_output:
            print(json.dumps(user_data, indent=2, default=str))
        else:
            print("👤 User details:")
            print(f"ID: {user_data['id']}")
            print(f"Phone: {user_data['phone_number']}")
            print(f"Starred Categories: {', '.join(user_data['starred_categories']) if user_data['starred_categories'] else 'None'}")
            print(f"Bookmarks: {len(user_data['bookmarks'])} items")
            if user_data['bookmarks']:
                print(f"  - {', '.join(user_data['bookmarks'])}")
            print(f"Cached Recommendations: {len(user_data['cached_recommendations'])} items")
            if user_data['cached_recommendations']:
                print(f"  - {', '.join(user_data['cached_recommendations'])}")
            print(f"Created: {user_data['created_at']}")
            print(f"Updated: {user_data['updated_at']}")
        
        db.close()
        
    except Exception as e:
        print(f"❌ Error getting user: {e}")
        sys.exit(1)


def get_user_by_phone(phone_number: str, db_path: Optional[str] = None, json_output: bool = False):
    """Get user by phone number."""
    try:
        db = DatabaseManager(db_path)
        user_data = db.get_user_by_phone(phone_number)
        
        if not user_data:
            print(f"❌ User with phone number {phone_number} not found.")
            sys.exit(1)
        
        if json_output:
            print(json.dumps(user_data, indent=2, default=str))
        else:
            print("📱 User details:")
            print(f"ID: {user_data['id']}")
            print(f"Phone: {user_data['phone_number']}")
            print(f"Starred Categories: {', '.join(user_data['starred_categories']) if user_data['starred_categories'] else 'None'}")
            print(f"Bookmarks: {len(user_data['bookmarks'])} items")
            print(f"Cached Recommendations: {len(user_data['cached_recommendations'])} items")
            print(f"Created: {user_data['created_at']}")
            print(f"Updated: {user_data['updated_at']}")
        
        db.close()
        
    except Exception as e:
        print(f"❌ Error getting user by phone: {e}")
        sys.exit(1)


def delete_user(user_id: str, db_path: Optional[str] = None):
    """Delete user by ID."""
    try:
        db = DatabaseManager(db_path)
        
        # First check if user exists
        user_data = db.get_user(user_id)
        if not user_data:
            print(f"❌ User with ID {user_id} not found.")
            sys.exit(1)
        
        # Confirm deletion
        print(f"⚠️  You are about to delete user:")
        print(f"   ID: {user_data['id']}")
        print(f"   Phone: {user_data['phone_number']}")
        print(f"   Created: {user_data['created_at']}")
        
        confirm = input("\n🗑️  Are you sure you want to delete this user? (yes/no): ").lower().strip()
        if confirm not in ['yes', 'y']:
            print("❌ Deletion cancelled.")
            sys.exit(0)
        
        deleted = db.delete_user(user_id)
        
        if deleted:
            print("✅ User deleted successfully!")
        else:
            print("❌ Failed to delete user.")
            sys.exit(1)
        
        db.close()
        
    except Exception as e:
        print(f"❌ Error deleting user: {e}")
        sys.exit(1)


def execute_query(query: str, db_path: Optional[str] = None, json_output: bool = False):
    """Execute custom SQL query."""
    try:
        db = DatabaseManager(db_path)
        conn = db._get_connection()
        
        # Execute the query
        if query.strip().upper().startswith(('SELECT', 'SHOW', 'DESCRIBE', 'PRAGMA')):
            # Read-only queries
            results = conn.execute(query).fetchall()
            
            if json_output:
                # Convert results to list of dicts for JSON output
                column_names = [desc[0] for desc in conn.description] if conn.description else []
                json_results = []
                for row in results:
                    json_results.append(dict(zip(column_names, row)))
                print(json.dumps(json_results, indent=2, default=str))
            else:
                if results:
                    # Print column headers if available
                    if conn.description:
                        headers = [desc[0] for desc in conn.description]
                        print(" | ".join(headers))
                        print("-" * (len(" | ".join(headers))))
                    
                    # Print results
                    for row in results:
                        print(" | ".join(str(cell) for cell in row))
                    
                    print(f"\n📊 {len(results)} row(s) returned.")
                else:
                    print("📊 Query executed successfully. No results returned.")
        else:
            # Write queries
            result = conn.execute(query)
            conn.commit()
            print(f"✅ Query executed successfully. {result.rowcount} row(s) affected.")
        
        db.close()
        
    except Exception as e:
        print(f"❌ Error executing query: {e}")
        sys.exit(1)


def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description="Database utility for DuckDB operations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Database management
  python db.py --init                           # Initialize database
  python db.py --count                          # Count users
  python db.py --list                           # List users
  python db.py --list --limit 5 --offset 10    # List with pagination
  
  # User operations
  python db.py --create-user +1234567890        # Create user
  python db.py --create-user +1234567890 --categories restaurant,cafe
  python db.py --get-user <user_id>             # Get user by ID
  python db.py --get-by-phone +1234567890       # Get user by phone
  python db.py --delete-user <user_id>          # Delete user
  
  # Custom queries
  python db.py --query "SELECT * FROM users"    # Custom query
  python db.py --query "SELECT COUNT(*) FROM users WHERE phone_number LIKE '+1%'"
  
  # JSON output
  python db.py --list --json                    # JSON output
  python db.py --get-user <user_id> --json      # JSON output
        """
    )
    
    # Database file option
    parser.add_argument(
        '--db-path',
        help='Path to DuckDB database file (default: uses app default)'
    )
    
    # Main actions (mutually exclusive)
    action_group = parser.add_mutually_exclusive_group(required=True)
    action_group.add_argument('--init', action='store_true', help='Initialize database schema')
    action_group.add_argument('--count', action='store_true', help='Count total users')
    action_group.add_argument('--list', action='store_true', help='List users')
    action_group.add_argument('--create-user', metavar='PHONE', help='Create user with phone number')
    action_group.add_argument('--get-user', metavar='USER_ID', help='Get user by ID')
    action_group.add_argument('--get-by-phone', metavar='PHONE', help='Get user by phone number')
    action_group.add_argument('--delete-user', metavar='USER_ID', help='Delete user by ID')
    action_group.add_argument('--query', metavar='SQL', help='Execute custom SQL query')
    
    # Options for create-user
    parser.add_argument(
        '--categories',
        help='Comma-separated list of starred categories for new user',
        default=''
    )
    
    # Options for list
    parser.add_argument('--limit', type=int, default=10, help='Limit results (default: 10)')
    parser.add_argument('--offset', type=int, default=0, help='Offset for pagination (default: 0)')
    
    # Output format
    parser.add_argument('--json', action='store_true', help='Output in JSON format')
    
    args = parser.parse_args()
    
    try:
        if args.init:
            init_database(args.db_path)
        
        elif args.count:
            count_users(args.db_path)
        
        elif args.list:
            list_users(args.db_path, args.limit, args.offset, args.json)
        
        elif args.create_user:
            categories = [cat.strip() for cat in args.categories.split(',') if cat.strip()] if args.categories else []
            create_user(args.create_user, categories, args.db_path)
        
        elif args.get_user:
            get_user(args.get_user, args.db_path, args.json)
        
        elif args.get_by_phone:
            get_user_by_phone(args.get_by_phone, args.db_path, args.json)
        
        elif args.delete_user:
            delete_user(args.delete_user, args.db_path)
        
        elif args.query:
            execute_query(args.query, args.db_path, args.json)
            
    except KeyboardInterrupt:
        print("\n⏹️  Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
