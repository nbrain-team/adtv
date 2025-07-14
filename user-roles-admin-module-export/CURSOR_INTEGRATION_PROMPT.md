# User Roles & Admin Dashboard Integration Prompt

## Project Context
I need to integrate a complete user management system with role-based access control into my AI-powered marketing campaign generator platform. The system should handle user authentication, authorization, role management, and provide an admin dashboard for managing users and their permissions.

## Source Module
I have a complete user roles and admin dashboard module exported from another project with the following structure:

```
user-roles-admin-module-export/
├── backend/
│   ├── auth.py                 # JWT authentication logic
│   ├── user_routes.py          # User management API endpoints
│   ├── database.py             # Complete database models
│   ├── user_models.py          # User model only
│   └── api_implementation.py   # Full API implementation
├── frontend/
│   ├── AuthContext.tsx         # React authentication context
│   ├── ProtectedRoute.tsx      # Route protection component
│   ├── ProfilePage.tsx         # User profile management
│   └── UserManagementComponent.tsx  # Admin dashboard
└── docs/
    └── INTEGRATION_GUIDE.md    # Detailed integration instructions
```

## Integration Requirements

### Backend Requirements
1. **FastAPI Integration**: Integrate the authentication and user management endpoints into my existing FastAPI application
2. **Database**: Set up PostgreSQL database with user tables and proper migrations
3. **JWT Authentication**: Implement JWT-based authentication with token expiration
4. **Role-Based Access**: Implement admin and user roles with granular permissions
5. **API Endpoints**: All user CRUD operations, authentication, and permission management

### Frontend Requirements
1. **React Integration**: Integrate the components into my existing React application
2. **Authentication Flow**: Login, signup, and logout functionality
3. **Protected Routes**: Route protection based on authentication and permissions
4. **Admin Dashboard**: Full user management interface for admins
5. **User Profile**: Allow users to manage their own profiles

### Permission System
The system should support these module-level permissions:
- `chat` - Access to AI chat functionality
- `history` - View conversation history
- `knowledge` - Access knowledge base
- `agents` - Create and manage AI agents
- `data-lake` - Access data lake features
- `user-management` - Manage users (admin only)

## Technical Stack
- **Backend**: FastAPI, SQLAlchemy, PostgreSQL, JWT (python-jose)
- **Frontend**: React, TypeScript, Radix UI, Axios
- **Authentication**: JWT tokens with Bearer authentication
- **Password Security**: bcrypt hashing

## Key Features to Implement

### 1. User Authentication
- JWT-based login/logout
- User registration with email validation
- Password reset functionality (optional)
- Token refresh mechanism

### 2. User Management (Admin)
- List all users with pagination
- Search and filter users
- Edit user details and roles
- Enable/disable user accounts
- Delete users
- Manage user permissions

### 3. User Profile
- View and edit own profile
- Change password
- View assigned permissions
- Track last login time

### 4. Security Features
- Password hashing with bcrypt
- JWT token expiration
- CORS configuration
- Rate limiting (optional)
- Audit logging (optional)

## Integration Steps

### Phase 1: Backend Setup
1. Install required dependencies
2. Set up database models and migrations
3. Configure environment variables
4. Integrate authentication middleware
5. Add user management API routes
6. Create initial admin user

### Phase 2: Frontend Setup
1. Install Radix UI and dependencies
2. Set up authentication context
3. Implement login/signup pages
4. Add protected route wrapper
5. Integrate user management dashboard
6. Update navigation with role-based menu items

### Phase 3: Testing & Deployment
1. Test all authentication flows
2. Verify permission checks
3. Test admin functionality
4. Set up production environment variables
5. Deploy with proper security configurations

## Specific Instructions

Please help me:

1. **Analyze my current project structure** and identify the best integration points for the user management system

2. **Set up the database** with proper migrations and create the initial admin user

3. **Integrate the authentication system** into my existing FastAPI backend, ensuring it works with my current API structure

4. **Implement the frontend components** with proper styling to match my existing UI

5. **Configure the permission system** to work with my specific modules (marketing campaigns, content generation, calendar, reporting)

6. **Add proper error handling** and user feedback for all authentication and authorization scenarios

7. **Ensure security best practices** are followed throughout the implementation

## Current Project Details
[Add your specific project details here, such as:]
- Main backend file location: `backend/main.py`
- Frontend entry point: `frontend/src/App.tsx`
- Database configuration: `backend/config/database.py`
- API base URL: `http://localhost:8000/api`
- Existing routes/modules: [List your current API routes]

## Expected Outcome
A fully integrated user management system that:
- Seamlessly integrates with my existing application
- Provides secure authentication and authorization
- Allows admins to manage users and permissions
- Protects routes and API endpoints based on roles
- Maintains a consistent UI/UX with my application

Please guide me through the integration process step by step, ensuring all components work together properly. 