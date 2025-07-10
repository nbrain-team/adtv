# User Roles & Admin Dashboard Integration Prompt

I need to integrate a complete user management system with role-based access control and admin dashboard into this project. I have a module folder called `user-roles-admin-module` that contains all the necessary components.

## Module Overview

This module provides:
- JWT-based authentication (login/signup)
- User roles (user/admin) with module-level permissions
- Complete admin dashboard for user management
- User profile management
- Active/inactive user status control

## Integration Requirements

### Backend Integration

1. **Database Setup**:
   - I need a PostgreSQL database with a users table
   - The module includes migration scripts in `backend/scripts/db_setup.py`
   - User model includes: email, password, role, permissions (JSON), profile fields, timestamps

2. **Authentication System**:
   - JWT token-based authentication
   - OAuth2PasswordBearer for API security
   - Protected routes with role/permission checks

3. **API Endpoints Needed**:
   - POST /signup - User registration
   - POST /login - User authentication  
   - GET /user/profile - Get current user
   - PUT /user/profile - Update profile
   - GET /user/users - List all users (admin)
   - PUT /user/users/{id}/permissions - Update permissions (admin)
   - PUT /user/users/{id}/toggle-active - Enable/disable user (admin)
   - DELETE /user/users/{id} - Delete user (admin)

### Frontend Integration

1. **Authentication Context**:
   - AuthProvider component to wrap the app
   - Manages token storage and user state
   - Provides login/logout functions

2. **Protected Routes**:
   - ProtectedRoute component for securing pages
   - Supports role-based (requireAdmin) and permission-based access
   - Shows access denied page for unauthorized users

3. **UI Components**:
   - LoginPage with email/password form
   - ProfilePage with:
     - User profile editing
     - Admin dashboard (if admin role)
     - User management table with permissions grid
     - Search, edit, activate/deactivate users

4. **Permission System**:
   - Module-based permissions stored as JSON
   - Default modules: chat, history, knowledge, agents, data-lake
   - Easily extensible for new features

## Integration Steps

Please help me:

1. **Set up the database**:
   - Create users table with all required fields
   - Run migration to add role/permissions columns
   - Set up initial admin user

2. **Integrate backend authentication**:
   - Add auth.py authentication logic
   - Set up user routes from user_routes.py
   - Configure JWT token handling
   - Add login/signup endpoints

3. **Integrate frontend components**:
   - Set up AuthContext provider
   - Add ProtectedRoute wrapper
   - Integrate LoginPage
   - Add ProfilePage with admin dashboard
   - Configure API client with auth headers

4. **Configure permissions**:
   - Define which modules/features need permissions
   - Update navigation to show/hide based on permissions
   - Add permission checks to protected features

5. **Style integration**:
   - The module uses Radix UI components
   - Ensure CSS variables are defined for theming
   - May need to adjust styles to match existing design

## Key Files in Module

**Backend:**
- `backend/core/auth.py` - Authentication logic
- `backend/core/database.py` - User model and DB setup
- `backend/core/user_routes.py` - User management endpoints
- `backend/main.py` - Simplified FastAPI app example
- `backend/scripts/db_setup.py` - Database migrations

**Frontend:**
- `frontend/src/context/AuthContext.tsx` - Auth state management
- `frontend/src/components/ProtectedRoute.tsx` - Route protection
- `frontend/src/pages/LoginPage.tsx` - Login UI
- `frontend/src/pages/ProfilePage.tsx` - Profile & admin dashboard
- `frontend/src/api.ts` - Axios configuration

## Environment Variables Needed

**Backend (.env):**
```
DATABASE_URL=postgresql://user:pass@localhost/dbname
SECRET_KEY=<generate-with-openssl-rand-hex-32>
```

**Frontend (.env):**
```
VITE_API_BASE_URL=http://localhost:8000
```

## Important Considerations

1. The module expects PostgreSQL database
2. Passwords are hashed with bcrypt
3. Admin users can manage all other users except themselves
4. Users cannot delete or deactivate their own accounts
5. The first admin should be created via the set_admin_user.py script

Please integrate this module while:
- Maintaining compatibility with existing code
- Preserving current functionality
- Following the project's coding standards
- Ensuring proper error handling
- Adding any necessary migrations for existing users

Let me know if you need any clarification about the module structure or integration approach! 