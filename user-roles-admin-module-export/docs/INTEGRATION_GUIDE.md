# User Roles & Admin Dashboard Module - Integration Guide

## Overview
This module provides a complete user management system with role-based access control (RBAC), authentication, and an admin dashboard for managing users and permissions.

## Features
- JWT-based authentication
- User registration and login
- Role-based access control (Admin/User roles)
- Permission management per module
- User profile management
- Admin dashboard for user management
- Activity tracking (last login)
- User search and filtering

## File Structure
```
user-roles-admin-module-export/
├── backend/
│   ├── auth.py                 # Authentication logic
│   ├── user_routes.py          # User API endpoints
│   ├── database.py             # Database models (full)
│   ├── user_models.py          # User model only
│   └── api_implementation.py   # Complete API implementation
├── frontend/
│   ├── AuthContext.tsx         # Authentication context
│   ├── ProtectedRoute.tsx      # Route protection component
│   ├── ProfilePage.tsx         # User profile page
│   └── UserManagementComponent.tsx  # Admin user management
└── docs/
    └── INTEGRATION_GUIDE.md    # This file
```

## Backend Integration

### 1. Install Dependencies
```bash
pip install fastapi sqlalchemy psycopg2-binary python-jose[cryptography] passlib[bcrypt] python-multipart
```

### 2. Environment Variables
Create a `.env` file:
```env
DATABASE_URL=postgresql://user:password@localhost/dbname
SECRET_KEY=your-secret-key-here-generate-with-openssl-rand-hex-32
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### 3. Database Setup
```python
# In your main.py or database initialization file
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from user_models import Base, User

# Create engine
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables
Base.metadata.create_all(bind=engine)

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### 4. Authentication Setup
```python
# auth.py integration
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Copy the auth.py file functions here
```

### 5. API Routes Integration
```python
# In your main.py
from fastapi import FastAPI
from user_routes import router as user_router

app = FastAPI()

# Include user routes
app.include_router(user_router, prefix="/api/user", tags=["users"])
```

### 6. Initial Admin User
```python
# Create initial admin user script
from sqlalchemy.orm import Session
from database import SessionLocal, User
from auth import get_password_hash

def create_admin_user():
    db = SessionLocal()
    
    # Check if admin exists
    admin = db.query(User).filter(User.email == "admin@example.com").first()
    if not admin:
        admin = User(
            email="admin@example.com",
            hashed_password=get_password_hash("admin123"),
            role="admin",
            permissions={
                "chat": True,
                "history": True,
                "knowledge": True,
                "agents": True,
                "data-lake": True,
                "user-management": True
            }
        )
        db.add(admin)
        db.commit()
        print("Admin user created!")
    db.close()

if __name__ == "__main__":
    create_admin_user()
```

## Frontend Integration

### 1. Install Dependencies
```bash
npm install @radix-ui/themes @radix-ui/react-icons axios
```

### 2. Authentication Context Setup
```tsx
// In your App.tsx or main component
import { AuthProvider } from './context/AuthContext';

function App() {
  return (
    <AuthProvider>
      {/* Your app components */}
    </AuthProvider>
  );
}
```

### 3. Protected Routes
```tsx
import { ProtectedRoute } from './components/ProtectedRoute';

// Use for protected pages
<ProtectedRoute requiredPermission="user-management">
  <UserManagementComponent />
</ProtectedRoute>
```

### 4. API Configuration
```typescript
// api.ts
import axios from 'axios';

const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000/api',
});

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export default api;
```

### 5. Navigation Integration
```tsx
// Add to your navigation component
{user?.role === 'admin' && (
  <NavigationMenu.Item>
    <NavigationMenu.Link href="/admin/users">
      User Management
    </NavigationMenu.Link>
  </NavigationMenu.Item>
)}
```

## Permission System

### Available Permissions
- `chat` - Access to AI chat functionality
- `history` - View conversation history
- `knowledge` - Access knowledge base
- `agents` - Create and manage AI agents
- `data-lake` - Access data lake features
- `user-management` - Manage users (admin only)

### Checking Permissions
```typescript
// Frontend
const hasPermission = (permission: string) => {
  return user?.permissions?.[permission] === true;
};

// Backend
def check_permission(user: User, permission: str) -> bool:
    return user.permissions.get(permission, False)
```

## Database Schema

### User Table
```sql
CREATE TABLE users (
    id VARCHAR PRIMARY KEY,
    email VARCHAR UNIQUE NOT NULL,
    hashed_password VARCHAR NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    first_name VARCHAR,
    last_name VARCHAR,
    company VARCHAR,
    website_url VARCHAR,
    role VARCHAR DEFAULT 'user',
    permissions JSON DEFAULT '{"chat": true}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP WITH TIME ZONE
);
```

## API Endpoints

### Authentication
- `POST /api/user/token` - Login
- `POST /api/user/signup` - Register new user

### User Profile
- `GET /api/user/profile` - Get current user profile
- `PUT /api/user/profile` - Update current user profile

### User Management (Admin Only)
- `GET /api/user/users` - List all users
- `GET /api/user/users/{user_id}` - Get specific user
- `PUT /api/user/users/{user_id}` - Update user
- `DELETE /api/user/users/{user_id}` - Delete user
- `PUT /api/user/users/{user_id}/permissions` - Update user permissions

## Security Considerations

1. **Password Security**
   - Passwords are hashed using bcrypt
   - Never store plain text passwords

2. **JWT Tokens**
   - Tokens expire after 30 minutes by default
   - Store tokens securely (httpOnly cookies recommended)

3. **CORS Configuration**
   ```python
   from fastapi.middleware.cors import CORSMiddleware
   
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["http://localhost:3000"],
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"],
   )
   ```

4. **Rate Limiting**
   Consider adding rate limiting to prevent brute force attacks

## Customization

### Adding New Permissions
1. Add to `AVAILABLE_PERMISSIONS` in frontend
2. Update default permissions in User model
3. Add permission checks in your routes

### Custom User Fields
1. Add fields to User model
2. Update UserCreate/UserUpdate schemas
3. Update frontend forms

### Styling
The frontend uses Radix UI. Customize theme in your app:
```tsx
import { Theme } from '@radix-ui/themes';

<Theme accentColor="blue" radius="medium">
  {/* Your app */}
</Theme>
```

## Troubleshooting

### Common Issues

1. **"No DATABASE_URL found"**
   - Ensure .env file exists and contains DATABASE_URL

2. **"Token expired"**
   - Implement token refresh or increase ACCESS_TOKEN_EXPIRE_MINUTES

3. **CORS errors**
   - Check CORS middleware configuration
   - Ensure frontend URL is in allowed origins

4. **"Permission denied"**
   - Check user role and permissions in database
   - Ensure token is being sent with requests

## Testing

### Backend Tests
```python
# test_auth.py
def test_create_user():
    # Test user creation
    pass

def test_login():
    # Test authentication
    pass

def test_permissions():
    # Test permission system
    pass
```

### Frontend Tests
```typescript
// UserManagement.test.tsx
describe('UserManagement', () => {
  it('should display users list', () => {
    // Test implementation
  });
});
```

## Support
For issues or questions, refer to the original implementation in the ADTV project. 