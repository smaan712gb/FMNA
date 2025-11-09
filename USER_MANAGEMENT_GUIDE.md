# FMNA Platform - User Management Guide

## ✅ User Management System - COMPLETE

The FMNA platform now includes a complete user authentication and management system.

## 🔐 Admin Account

**Email:** smaan2011@gmail.com  
**Default Password:** admin123  
**⚠️ IMPORTANT:** Change this password immediately after first login!

## 🚀 Quick Start

### 1. Start the Platform
```powershell
cd c:\Users\smaan\OneDrive\fmna
conda activate fmna
streamlit run frontend_app.py
```

### 2. Login as Admin
- Open the browser (usually http://localhost:8501)
- Login with:
  - Email: smaan2011@gmail.com
  - Password: admin123

### 3. Change Admin Password (REQUIRED)
- Navigate to **⚙️ Settings** page
- Use the "Change Password" section
- Enter current password: admin123
- Enter and confirm your new secure password
- Click "Change Password"

### 4. Add New Users
- Navigate to **👥 User Management** page (admin only)
- Fill in the form:
  - Email: user's email address
  - Password: minimum 8 characters (share this with the user)
  - Role: "user" or "admin"
- Click "Create User"
- Send credentials to the user securely

## 👤 User Roles

### Admin Role
- Full access to all platform features
- Can add/delete users
- Can enable/disable user accounts
- Can view login history
- Access to User Management page

### User Role
- Access to all analysis features
- Can run analyses
- Can use AI Q&A
- Can view results
- Can download outputs
- Cannot manage other users

## 📋 Features

### Admin Features

#### User Management
- ➕ **Add Users:** Create new user accounts with email and password
- 🗑️ **Delete Users:** Remove user accounts (cannot delete admin)
- 🔄 **Toggle Status:** Enable/disable user accounts
- 📊 **Login History:** View all login attempts and activity
- 👥 **User List:** See all users, their roles, and last login times

#### Security Features
- 🔐 **Password Encryption:** All passwords are hashed with PBKDF2-HMAC-SHA256
- 🔑 **Salt:** Each password uses a unique 32-byte salt
- 📝 **Login Tracking:** All authentication attempts are logged
- 🚪 **Session Management:** Secure session handling
- ⏸️ **Account Locking:** Ability to disable compromised accounts

### User Features

#### Platform Access
- 📊 **New Analysis:** Run comprehensive financial analyses
- 💬 **AI Q&A:** Ask questions about analysis results
- 📈 **View Results:** Access detailed valuation and due diligence reports
- 📥 **Download Outputs:** Get Excel, PowerPoint, and PDF reports
- 🏠 **Dashboard:** Overview of recent activity

#### Account Management
- 🔐 **Change Password:** Users can change their own passwords
- 🚪 **Logout:** Secure session termination

## 🔒 Security Best Practices

### For Admins

1. **Change Default Password Immediately**
   - The default password "admin123" must be changed
   - Use a strong password (12+ characters, mixed case, numbers, symbols)

2. **User Password Policy**
   - Require minimum 8 characters
   - Share passwords securely (encrypted email, password manager)
   - Encourage users to change passwords on first login

3. **Account Monitoring**
   - Regularly review login history
   - Check for failed login attempts
   - Disable inactive accounts

4. **Principle of Least Privilege**
   - Only grant admin role when necessary
   - Most users should have "user" role

### For Users

1. **Password Security**
   - Use a unique password for FMNA platform
   - Do not share passwords
   - Change password if compromised

2. **Session Security**
   - Always logout when done
   - Do not leave sessions unattended
   - Report suspicious activity

## 📂 Database

User data is stored in: `data/users.db`

**Database Schema:**

### users table
- id (PRIMARY KEY)
- email (UNIQUE, NOT NULL)
- password_hash (NOT NULL)
- salt (NOT NULL)
- role (NOT NULL, default: 'user')
- is_active (NOT NULL, default: 1)
- created_at (TIMESTAMP)
- last_login (TIMESTAMP)
- created_by (TEXT)

### login_history table
- id (PRIMARY KEY)
- email (NOT NULL)
- login_time (TIMESTAMP)
- ip_address (TEXT)
- success (BOOLEAN NOT NULL)

## 🛠️ Troubleshooting

### Cannot Login
- Verify email is correct (case-sensitive)
- Check if account is active (admin can check)
- Ensure password is correct
- Contact admin for password reset

### Forgot Password
- Contact admin (smaan2011@gmail.com)
- Admin can delete old account and create new one
- Or admin can share a temporary password

### User Database Corrupted
```powershell
# Backup first
copy data\users.db data\users_backup.db

# Delete and recreate
del data\users.db
python auth\user_manager.py
```

### Need to Reset Admin Password
```python
# Run this in Python to reset admin password
from auth.user_manager import UserManager

um = UserManager()
# Delete admin
um.delete_user("smaan2011@gmail.com", "system")
# Will recreate with default password on next startup
```

## 📊 Usage Examples

### Example 1: Adding a New Analyst
1. Login as admin
2. Go to User Management
3. Add user:
   - Email: analyst@company.com
   - Password: TempPass123!
   - Role: user
4. Send email to analyst:
   ```
   Welcome to FMNA Platform!
   
   Login: http://localhost:8501
   Email: analyst@company.com
   Password: TempPass123!
   
   Please change your password after first login.
   ```

### Example 2: Disabling a User
1. Login as admin
2. Go to User Management
3. Find user in list
4. Click "Toggle" button to disable
5. User will not be able to login

### Example 3: Viewing Login History
1. Login as admin
2. Go to User Management
3. Expand "Recent Login Activity"
4. Review attempts:
   - ✅ = successful login
   - ❌ = failed login

## 🔄 API Reference

The UserManager class provides these methods:

```python
from auth.user_manager import UserManager

um = UserManager()

# Authentication
user_info = um.authenticate(email, password, ip_address)

# User Management
um.add_user(email, password, role="user", created_by=None)
um.delete_user(email, deleted_by=None)
um.toggle_user_status(email, admin_email)
um.user_exists(email)
um.get_all_users()

# Password Management
um.change_password(email, old_password, new_password)

# History
um.get_login_history(email=None, limit=50)
```

## ✨ Features Summary

✅ **Secure Authentication** - Password hashing with salt  
✅ **Role-Based Access** - Admin and User roles  
✅ **User Management UI** - Easy-to-use Streamlit interface  
✅ **Login History** - Track all authentication attempts  
✅ **Password Management** - Users can change their passwords  
✅ **Account Control** - Enable/disable user accounts  
✅ **Session Tracking** - Secure session management  
✅ **Admin Protection** - Cannot delete admin account  

## 📞 Support

For issues or questions:
- **Admin:** smaan2011@gmail.com
- **Documentation:** This guide
- **Technical Issues:** Check logs in terminal

---

**System Version:** 1.0  
**Last Updated:** November 7, 2025  
**Status:** ✅ Production Ready
