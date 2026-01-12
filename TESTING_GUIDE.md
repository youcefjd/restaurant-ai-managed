# Testing Guide - Authentication System
## How to Test What We Built

**Date**: January 11, 2026
**Status**: ✅ Authentication Complete - Ready to Test!

---

## 🚀 What's Running

### Backend API
- **URL**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Status**: ✅ Running with authentication

### Frontend App
- **URL**: http://localhost:5173
- **Status**: ✅ Running with auth pages

---

## 🧪 Test Plan

### Test 1: Restaurant Signup & Login

#### Step 1: Create New Restaurant Account
1. Open browser: http://localhost:5173
2. Click "Start Free Trial" or go to http://localhost:5173/signup
3. Fill in the form:
   - Restaurant Name: "Test Pizza Place"
   - Email: "test@pizza.com"
   - Phone: "555-0100"
   - Password: "password123"
4. Click "Start Free Trial"

**Expected Result:**
- ✅ Redirects to `/restaurant/dashboard`
- ✅ Shows "Test Pizza Place" in sidebar
- ✅ Shows "Free Trial - 30 days left"
- ✅ Logout button visible

#### Step 2: Test Logout
1. Click "Logout" button in sidebar
2. Should redirect to landing page

**Expected Result:**
- ✅ Logged out
- ✅ Redirected to `/`
- ✅ Token removed from localStorage

#### Step 3: Test Login
1. Go to http://localhost:5173/login
2. Enter credentials:
   - Email: "test@pizza.com"
   - Password: "password123"
3. Click "Sign In"

**Expected Result:**
- ✅ Redirects to `/restaurant/dashboard`
- ✅ Shows correct restaurant name
- ✅ All dashboard features work

#### Step 4: Test Protected Routes
1. Logout
2. Try to go directly to http://localhost:5173/restaurant/orders

**Expected Result:**
- ✅ Redirects to `/` (not logged in)
- ✅ Cannot access protected routes

---

### Test 2: Admin Login

#### Step 1: Admin Login
1. Go to http://localhost:5173/admin-login
2. Enter credentials:
   - Email: "admin@restaurantai.com"
   - Password: "admin123"
3. Click "Admin Sign In"

**Expected Result:**
- ✅ Redirects to `/admin/dashboard`
- ✅ Shows platform stats
- ✅ Shows "Platform Admin" in sidebar
- ✅ Logout button visible

#### Step 2: Test Admin Access
1. Click "Restaurants" in sidebar
2. Should see list of all restaurants (including "Test Pizza Place")

**Expected Result:**
- ✅ Can see all restaurants
- ✅ Can see their data
- ✅ Suspend/Activate buttons visible

#### Step 3: Test Role Separation
1. While logged in as admin
2. Try to go to http://localhost:5173/restaurant/dashboard

**Expected Result:**
- ✅ Redirected to `/admin/dashboard` (wrong role)
- ✅ Admins cannot access restaurant portal

---

### Test 3: Multiple Sessions

#### Step 1: Two Restaurants
1. Signup as Restaurant #1:
   - Name: "Pizza Palace"
   - Email: "pizza@palace.com"
   - Password: "password123"
2. Logout
3. Signup as Restaurant #2:
   - Name: "Burger House"
   - Email: "burger@house.com"
   - Password: "password123"

#### Step 2: Test Data Isolation
1. Login as "Pizza Palace"
2. Go to Orders page
3. Should see ONLY Pizza Palace's orders (if any)

4. Logout and login as "Burger House"
5. Go to Orders page
6. Should see ONLY Burger House's orders

**Expected Result:**
- ✅ Restaurants cannot see each other's data
- ✅ Data properly isolated by account_id

---

### Test 4: Token Expiration

#### Manual Test:
1. Login to any account
2. Open Browser DevTools → Application → Local Storage
3. Delete the `auth_token` key
4. Try to navigate to any protected page

**Expected Result:**
- ✅ Redirects to login page
- ✅ Shows "not authenticated" error

---

## 🔍 What to Look For

### ✅ Working Features:
- [ ] Signup creates account and logs in
- [ ] Login works with correct credentials
- [ ] Login fails with wrong credentials
- [ ] Logout clears session
- [ ] Protected routes redirect when not logged in
- [ ] Restaurant sees only their data
- [ ] Admin sees all data
- [ ] Role separation works (admin ≠ restaurant)
- [ ] Token included in API requests
- [ ] Business name shows correctly
- [ ] Trial days countdown shows

### ❌ Known Limitations:
- No "Forgot Password" yet
- Admin hardcoded (not in database)
- No email verification
- No password reset
- No "Remember Me" option
- Orders page will be empty (haven't made orders yet)

---

## 🐛 Common Issues & Fixes

### Issue: "Could not validate credentials"
**Fix:** Token expired or invalid. Logout and login again.

### Issue: Page keeps redirecting
**Fix:** Check browser console for errors. Clear localStorage and refresh.

### Issue: API 401 error
**Fix:** Backend may have restarted. Login again to get new token.

### Issue: Can't see restaurant data
**Fix:** Make sure you're logged in as the right restaurant account.

---

## 📊 Database Check

### View Created Accounts (SQLite):
```bash
cd /Users/youcef/restaurant-assistant
sqlite3 restaurant_reservations.db

# List all restaurant accounts
SELECT id, business_name, owner_email, subscription_status
FROM restaurant_accounts;

# Check if password is hashed
SELECT business_name, password_hash
FROM restaurant_accounts
LIMIT 1;

# Exit
.quit
```

**Expected:**
- Passwords should be hashed (long random string)
- NOT plain text

---

## 🧪 API Testing (Advanced)

### Test Signup API Directly:
```bash
curl -X POST http://localhost:8000/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "business_name": "API Test Restaurant",
    "owner_email": "api@test.com",
    "password": "testpass123",
    "phone": "555-0200"
  }'
```

### Test Login API:
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=api@test.com&password=testpass123"
```

### Test Protected Endpoint:
```bash
# Get token from login response, then:
curl -X GET http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

---

## ✅ Success Checklist

After testing, you should be able to:

- [x] **Authentication Backend** - JWT tokens working
- [ ] **Signup Flow** - New restaurants can signup
- [ ] **Login Flow** - Existing users can login
- [ ] **Logout Flow** - Sessions properly cleared
- [ ] **Protected Routes** - Cannot access without login
- [ ] **Role Separation** - Admin vs Restaurant access control
- [ ] **Data Isolation** - Restaurants see only their data
- [ ] **Token Refresh** - Auto-logout on token expiry
- [ ] **UI/UX** - Login pages look good
- [ ] **Error Handling** - Clear error messages

---

## 🎯 Next Steps After Testing

Once authentication works:

1. **Week 1 Remaining:**
   - [ ] Migrate to PostgreSQL
   - [ ] Redesign restaurant dashboard for tablets
   - [ ] Redesign admin dashboard with drill-down
   - [ ] Deploy to DigitalOcean
   - [ ] Add HTTPS/SSL

2. **Week 2:**
   - [ ] Integrate local LLMs (Ollama)
   - [ ] Integrate Whisper for speech-to-text
   - [ ] Remove Claude API dependency
   - [ ] Remove Twilio transcription dependency

---

## 📞 Test Credentials Summary

### Restaurant (Create via Signup):
- Any email/password you choose during signup

### Admin (Hardcoded):
- Email: `admin@restaurantai.com`
- Password: `admin123`

---

## 🎬 Ready to Test!

**Start here:**
1. Open http://localhost:5173
2. Click "Start Free Trial"
3. Create your first restaurant account
4. Explore the dashboard!

Then test admin access:
1. Logout
2. Go to http://localhost:5173/admin-login
3. Login with admin credentials
4. See all restaurants in the platform

**Have fun testing! Report any bugs you find.**
