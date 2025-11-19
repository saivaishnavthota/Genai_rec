# 🔑 User Credentials - GenAI Hiring System

**Last Updated:** October 8, 2025  
**Status:** ✅ All passwords reset to `test123`

---

## 📋 Active User Accounts

### 1. Account Manager
- **Email:** `voyageuraryan@gmail.com`
- **Password:** `test123`
- **Name:** Sai Aryan
- **Role:** Account Manager
- **Permissions:** 
  - Create and manage job postings
  - View applications
  - Use AI features for job generation

### 2. HR User
- **Email:** `test@example.com`
- **Password:** `test123`
- **Name:** Test User
- **Role:** HR
- **Permissions:**
  - Review applications
  - Schedule interviews
  - Make hiring decisions
  - Send notifications

### 3. Admin
- **Email:** `admin@genaisolutions.com`
- **Password:** `test123`
- **Name:** System Administrator
- **Role:** Admin
- **Permissions:**
  - Full system access
  - User management
  - System configuration
  - All features

---

## 🌐 Login Information

### Access URLs
- **Frontend:** http://localhost:6003 or http://149.102.158.71:6003
- **Backend API:** http://localhost:6002 or http://149.102.158.71:6002
- **API Docs:** http://localhost:6002/docs or http://149.102.158.71:6002/docs

### Login Steps
1. Go to http://149.102.158.71:6003 (or http://localhost:6003)
2. Click "Login" or navigate to login page
3. Enter one of the emails above
4. Enter password: `test123`
5. Click "Sign In"

---

## 🔄 Password Reset History

| Date | Action | Password | Users Affected |
|------|--------|----------|----------------|
| Oct 8, 2025 | Reset all passwords | `test123` | All 3 users |
| Oct 7, 2025 | Database restored from backup | - | - |

---

## 🔐 Security Recommendations

### For Development/Testing
✅ Current password (`test123`) is fine for local development

### For Production
⚠️ **IMPORTANT:** Change all passwords before deploying to production!

**Recommended actions:**
1. **After first login:** Each user should change their password
2. **Strong passwords:** Use passwords with:
   - At least 12 characters
   - Mix of uppercase, lowercase, numbers, symbols
   - No common words or patterns
3. **Different passwords:** Each user should have a unique password

### How to Change Password
1. Log in to the application
2. Go to Profile/Settings
3. Look for "Change Password" option
4. Enter current password: `test123`
5. Enter new strong password
6. Confirm new password

---

## 📊 User Roles & Capabilities

### Account Manager
Can perform:
- ✅ Create job postings
- ✅ Use AI to generate job descriptions
- ✅ View applications for their jobs
- ✅ Manage company profile
- ❌ Cannot schedule interviews (HR only)
- ❌ Cannot make final hiring decisions (HR only)

### HR
Can perform:
- ✅ View all applications
- ✅ Review and score candidates
- ✅ Schedule interviews
- ✅ Send interview invitations
- ✅ Make hiring decisions
- ✅ Access all HR features
- ❌ Cannot create/edit jobs (Account Manager only)

### Admin
Can perform:
- ✅ Everything Account Managers can do
- ✅ Everything HR can do
- ✅ Manage all users
- ✅ System configuration
- ✅ Access all features
- ✅ View system logs and analytics

---

## 🔍 Testing Workflows

### Test as Account Manager
```
Email: voyageuraryan@gmail.com
Password: test123

Test scenarios:
1. Create a new job posting
2. Use AI to generate job description
3. View applications for your jobs
4. Update company profile
```

### Test as HR
```
Email: test@example.com
Password: test123

Test scenarios:
1. Review incoming applications
2. Score candidates
3. Schedule interviews
4. Send interview invitations
5. Make hiring decisions
```

### Test as Admin
```
Email: admin@genaisolutions.com
Password: test123

Test scenarios:
1. Access all features
2. View system statistics
3. Manage users (if implemented)
4. Configure system settings
```

---

## 🆘 Troubleshooting

### Can't Log In?

**Problem:** "Invalid email or password"
- ✅ Double-check email spelling (copy from above)
- ✅ Password is: `test123` (lowercase, no spaces)
- ✅ Make sure backend is running: `docker-compose ps`
- ✅ Check backend logs: `docker-compose logs backend`

**Problem:** "User not found"
- ✅ Verify users exist in database:
  ```bash
  docker exec genai-postgres psql -U postgres -d genai_hiring -c "SELECT email FROM users;"
  ```

**Problem:** Page won't load
- ✅ Check frontend is running: `curl http://149.102.158.71:6003`
- ✅ Check backend API: `curl http://149.102.158.71:6002/health`
- ✅ View logs: `docker-compose logs -f`

### Reset Password Again

If you need to reset passwords again:

```bash
# Generate new hash for password "newpassword"
docker exec genai-backend python3 -c "import bcrypt; print(bcrypt.hashpw(b'newpassword', bcrypt.gensalt()).decode())"

# Update all users (replace HASH with output from above)
docker exec genai-postgres psql -U postgres -d genai_hiring -c "UPDATE users SET hashed_password = 'HASH';"
```

---

## 📝 Notes

### Password Storage
- Passwords are stored as **bcrypt hashes** (very secure!)
- Original passwords **cannot be retrieved** from the database
- Hash example: `$2b$12$KlaXwjMXWTj55/iCrN.BZuPXg9AJKpUVJnbpz4CpYEPfL8HyF1Hba`

### Password Verification
When you log in, the system:
1. Takes your entered password
2. Hashes it using bcrypt
3. Compares the hash with the stored hash
4. If they match, you're logged in!

### Creating New Users
To create additional users, you would typically:
1. Log in as Admin
2. Go to User Management
3. Add new user with email and temporary password
4. User changes password on first login

---

## ⚠️ SECURITY WARNING

**THIS FILE CONTAINS SENSITIVE INFORMATION!**

### Do NOT:
- ❌ Commit this file to Git
- ❌ Share this file publicly
- ❌ Send passwords via email/chat
- ❌ Use these passwords in production

### Do:
- ✅ Keep this file secure on your local machine
- ✅ Delete or update before production deployment
- ✅ Use environment-specific credentials
- ✅ Implement proper password policies

---

## 🎯 Quick Reference

**All Passwords:** `test123`

**Account Manager:** voyageuraryan@gmail.com  
**HR User:** test@example.com  
**Admin:** admin@genaisolutions.com  

**Login URL:** http://149.102.158.71:6003

---

**Created:** October 8, 2025  
**Purpose:** Development & Testing  
**Environment:** Production (149.102.158.71)  
**Status:** Active ✅

