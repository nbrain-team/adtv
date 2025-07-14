# User Roles & Admin Dashboard Module

A complete user management system with role-based access control (RBAC) for FastAPI + React applications.

## Quick Start

### For Integration into a New Project

1. **Copy this entire folder** to your new Cursor project
2. **Open the `CURSOR_INTEGRATION_PROMPT.md`** file
3. **Copy its contents** and use it as your initial prompt in the new Cursor window
4. **Follow the integration guide** in `docs/INTEGRATION_GUIDE.md`

## Module Contents

### Backend Components
- **JWT Authentication** - Secure token-based authentication
- **User Management API** - Complete CRUD operations for users
- **Role-Based Access Control** - Admin and user roles
- **Permission System** - Granular module-level permissions
- **Database Models** - SQLAlchemy models for PostgreSQL

### Frontend Components
- **Authentication Context** - React context for auth state
- **Protected Routes** - Route protection based on permissions
- **User Management Dashboard** - Admin interface for managing users
- **Profile Management** - User profile editing
- **Login/Signup Forms** - Authentication UI components

## Features

- ✅ JWT-based authentication with token expiration
- ✅ User registration and login
- ✅ Admin and user roles
- ✅ Granular permission management
- ✅ User profile management
- ✅ Admin dashboard for user management
- ✅ Search and filter users
- ✅ Enable/disable user accounts
- ✅ Activity tracking (last login)
- ✅ Secure password hashing (bcrypt)
- ✅ CORS support
- ✅ TypeScript support

## Tech Stack

**Backend:**
- FastAPI
- SQLAlchemy
- PostgreSQL
- JWT (python-jose)
- Passlib + bcrypt

**Frontend:**
- React 18
- TypeScript
- Radix UI
- Axios
- React Router

## File Structure

```
├── backend/
│   ├── auth.py                    # Authentication logic
│   ├── user_routes.py            # User API endpoints
│   ├── database.py               # Full database models
│   ├── user_models.py            # User model only
│   ├── api_implementation.py     # Complete API implementation
│   ├── db_setup.py              # Database migrations
│   └── requirements.txt         # Python dependencies
├── frontend/
│   ├── AuthContext.tsx          # Authentication context
│   ├── ProtectedRoute.tsx       # Route protection
│   ├── ProfilePage.tsx          # User profile page
│   ├── UserManagementComponent.tsx # Admin dashboard
│   └── package.json             # Node dependencies
├── docs/
│   └── INTEGRATION_GUIDE.md     # Detailed integration guide
├── CURSOR_INTEGRATION_PROMPT.md # Prompt for new Cursor project
└── README.md                    # This file
```

## Permissions

The module supports these permissions:
- `chat` - Access to AI chat functionality
- `history` - View conversation history
- `knowledge` - Access knowledge base
- `agents` - Create and manage AI agents
- `data-lake` - Access data lake features
- `user-management` - Manage users (admin only)

## API Endpoints

### Authentication
- `POST /api/user/token` - Login
- `POST /api/user/signup` - Register

### User Profile
- `GET /api/user/profile` - Get current user
- `PUT /api/user/profile` - Update profile

### User Management (Admin)
- `GET /api/user/users` - List users
- `GET /api/user/users/{id}` - Get user
- `PUT /api/user/users/{id}` - Update user
- `DELETE /api/user/users/{id}` - Delete user
- `PUT /api/user/users/{id}/permissions` - Update permissions

## Security

- Passwords hashed with bcrypt
- JWT tokens with expiration
- CORS configuration included
- Admin-only endpoints protected
- SQL injection prevention via SQLAlchemy

## License

This module is extracted from the ADTV project for reuse in other applications. 