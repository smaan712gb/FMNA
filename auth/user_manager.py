"""
Simple User Management System for FMNA Platform
Admin: smaan2011@gmail.com can add/delete users
"""

import sqlite3
import hashlib
import secrets
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
from loguru import logger

class UserManager:
    """Manages user authentication and authorization"""
    
    def __init__(self, db_path: str = "data/users.db"):
        """Initialize user manager with database"""
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
        self._ensure_admin_exists()
    
    def _init_database(self):
        """Initialize user database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'user',
                is_active BOOLEAN NOT NULL DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                created_by TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS login_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL,
                login_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ip_address TEXT,
                success BOOLEAN NOT NULL
            )
        """)
        
        conn.commit()
        conn.close()
        logger.info("User database initialized")
    
    def _ensure_admin_exists(self):
        """Ensure admin user exists"""
        admin_email = "smaan2011@gmail.com"
        
        if not self.user_exists(admin_email):
            # Create admin with default password "admin123" - should be changed on first login
            self.add_user(
                email=admin_email,
                password="admin123",
                role="admin",
                created_by="system"
            )
            logger.warning(f"Admin user created: {admin_email} with default password 'admin123' - CHANGE THIS!")
    
    def _hash_password(self, password: str, salt: str = None) -> tuple:
        """Hash password with salt"""
        if salt is None:
            salt = secrets.token_hex(32)
        
        password_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000
        ).hex()
        
        return password_hash, salt
    
    def add_user(self, email: str, password: str, role: str = "user", created_by: str = None) -> bool:
        """Add a new user"""
        try:
            if self.user_exists(email):
                logger.warning(f"User already exists: {email}")
                return False
            
            # Hash password
            password_hash, salt = self._hash_password(password)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO users (email, password_hash, salt, role, created_by)
                VALUES (?, ?, ?, ?, ?)
            """, (email, password_hash, salt, role, created_by))
            
            conn.commit()
            conn.close()
            
            logger.success(f"User created: {email} (role: {role})")
            return True
            
        except Exception as e:
            logger.error(f"Error adding user: {e}")
            return False
    
    def delete_user(self, email: str, deleted_by: str = None) -> bool:
        """Delete a user (cannot delete admin)"""
        try:
            if email == "smaan2011@gmail.com":
                logger.warning("Cannot delete admin user")
                return False
            
            if not self.user_exists(email):
                logger.warning(f"User does not exist: {email}")
                return False
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM users WHERE email = ?", (email,))
            
            conn.commit()
            conn.close()
            
            logger.success(f"User deleted: {email} by {deleted_by}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting user: {e}")
            return False
    
    def authenticate(self, email: str, password: str, ip_address: str = None) -> Optional[Dict[str, Any]]:
        """Authenticate user and return user info if successful"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT password_hash, salt, role, is_active
                FROM users
                WHERE email = ?
            """, (email,))
            
            result = cursor.fetchone()
            
            if not result:
                self._log_login_attempt(email, ip_address, success=False)
                return None
            
            stored_hash, salt, role, is_active = result
            
            if not is_active:
                logger.warning(f"Inactive user tried to login: {email}")
                self._log_login_attempt(email, ip_address, success=False)
                return None
            
            # Verify password
            password_hash, _ = self._hash_password(password, salt)
            
            if password_hash == stored_hash:
                # Update last login
                cursor.execute("""
                    UPDATE users
                    SET last_login = CURRENT_TIMESTAMP
                    WHERE email = ?
                """, (email,))
                conn.commit()
                
                self._log_login_attempt(email, ip_address, success=True)
                
                user_info = {
                    'email': email,
                    'role': role,
                    'is_admin': role == 'admin'
                }
                
                logger.success(f"User authenticated: {email}")
                conn.close()
                return user_info
            else:
                self._log_login_attempt(email, ip_address, success=False)
                conn.close()
                return None
                
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return None
    
    def _log_login_attempt(self, email: str, ip_address: str, success: bool):
        """Log login attempt"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO login_history (email, ip_address, success)
                VALUES (?, ?, ?)
            """, (email, ip_address, success))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error logging login attempt: {e}")
    
    def user_exists(self, email: str) -> bool:
        """Check if user exists"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT 1 FROM users WHERE email = ?", (email,))
            result = cursor.fetchone()
            
            conn.close()
            return result is not None
            
        except Exception as e:
            logger.error(f"Error checking user existence: {e}")
            return False
    
    def get_all_users(self) -> List[Dict[str, Any]]:
        """Get all users (admin only)"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT email, role, is_active, created_at, last_login, created_by
                FROM users
                ORDER BY created_at DESC
            """)
            
            users = []
            for row in cursor.fetchall():
                users.append({
                    'email': row[0],
                    'role': row[1],
                    'is_active': bool(row[2]),
                    'created_at': row[3],
                    'last_login': row[4],
                    'created_by': row[5]
                })
            
            conn.close()
            return users
            
        except Exception as e:
            logger.error(f"Error getting users: {e}")
            return []
    
    def change_password(self, email: str, old_password: str, new_password: str) -> bool:
        """Change user password"""
        try:
            # Verify old password first
            if not self.authenticate(email, old_password):
                logger.warning(f"Password change failed: incorrect old password for {email}")
                return False
            
            # Hash new password
            password_hash, salt = self._hash_password(new_password)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE users
                SET password_hash = ?, salt = ?
                WHERE email = ?
            """, (password_hash, salt, email))
            
            conn.commit()
            conn.close()
            
            logger.success(f"Password changed for: {email}")
            return True
            
        except Exception as e:
            logger.error(f"Error changing password: {e}")
            return False
    
    def toggle_user_status(self, email: str, admin_email: str) -> bool:
        """Toggle user active/inactive status (admin only)"""
        try:
            if email == "smaan2011@gmail.com":
                logger.warning("Cannot deactivate admin user")
                return False
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE users
                SET is_active = NOT is_active
                WHERE email = ?
            """, (email,))
            
            conn.commit()
            conn.close()
            
            logger.success(f"User status toggled: {email} by {admin_email}")
            return True
            
        except Exception as e:
            logger.error(f"Error toggling user status: {e}")
            return False
    
    def get_login_history(self, email: str = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Get login history"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if email:
                cursor.execute("""
                    SELECT email, login_time, ip_address, success
                    FROM login_history
                    WHERE email = ?
                    ORDER BY login_time DESC
                    LIMIT ?
                """, (email, limit))
            else:
                cursor.execute("""
                    SELECT email, login_time, ip_address, success
                    FROM login_history
                    ORDER BY login_time DESC
                    LIMIT ?
                """, (limit,))
            
            history = []
            for row in cursor.fetchall():
                history.append({
                    'email': row[0],
                    'login_time': row[1],
                    'ip_address': row[2],
                    'success': bool(row[3])
                })
            
            conn.close()
            return history
            
        except Exception as e:
            logger.error(f"Error getting login history: {e}")
            return []


# Convenience functions
def get_user_manager() -> UserManager:
    """Get user manager instance"""
    return UserManager()


if __name__ == "__main__":
    # Test the user manager
    print("="*80)
    print("FMNA User Management System - Test")
    print("="*80)
    
    um = UserManager()
    
    # Test admin login
    print("\n1. Testing admin login...")
    admin = um.authenticate("smaan2011@gmail.com", "admin123")
    if admin:
        print(f"✅ Admin authenticated: {admin}")
    else:
        print("❌ Admin authentication failed")
    
    # Test adding user
    print("\n2. Testing add user...")
    if um.add_user("testuser@example.com", "password123", role="user", created_by="smaan2011@gmail.com"):
        print("✅ User added successfully")
    
    # Test listing users
    print("\n3. Listing all users...")
    users = um.get_all_users()
    for user in users:
        print(f"  - {user['email']} ({user['role']}) - Active: {user['is_active']}")
    
    # Test user login
    print("\n4. Testing user login...")
    user = um.authenticate("testuser@example.com", "password123")
    if user:
        print(f"✅ User authenticated: {user}")
    else:
        print("❌ User authentication failed")
    
    print("\n" + "="*80)
    print("⚠️  IMPORTANT: Change admin password from default 'admin123'!")
    print("="*80)
