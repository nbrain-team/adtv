# User Roles & Admin Dashboard Module

A complete user management system with role-based access control and admin dashboard functionality.

## Features

- **User Authentication**: JWT-based authentication system
- **Role Management**: User and Admin roles
- **Permission System**: Module-level permissions for granular access control
- **Admin Dashboard**: Complete user management interface
- **User Profile Management**: Self-service profile updates
- **Active/Inactive Status**: Enable/disable user accounts
- **Secure Password Handling**: Bcrypt password hashing

## Module Structure

```
user-roles-admin-module/
├── backend/
│   ├── core/
│   │   ├── auth.py          # Authentication logic
│   │   ├── database.py      # Database models and connection
│   │   └── user_routes.py   # User management API endpoints
│   ├── scripts/
│   │   ├── db_setup.py      # Database migration script
│   │   └── set_admin_user.py # Admin user setup script
│   ├── main.py              # FastAPI application
│   └── requirements.txt     # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   └── ProtectedRoute.tsx  # Route protection component
│   │   ├── context/
│   │   │   └── AuthContext.tsx     # Authentication context
│   │   ├── pages/
│   │   │   ├── LoginPage.tsx       # Login interface
│   │   │   └── ProfilePage.tsx     # User profile & admin dashboard
│   │   └── api.ts                  # API client configuration
│   └── package.json         # Frontend dependencies
└── README.md
```

## Database Schema

### Users Table
```sql
- id: UUID (Primary Key)
- email: String (Unique)
- hashed_password: String
- is_active: Boolean (default: true)
- first_name: String (nullable)
- last_name: String (nullable)
- company: String (nullable)
- website_url: String (nullable)
- role: String (default: "user") ["user", "admin"]
- permissions: JSON (default: {"chat": true})
- created_at: Timestamp
- last_login: Timestamp (nullable)
```

## Available Permissions

The module supports the following permission keys:
- `chat`: Access to chat functionality
- `history`: Access to chat history
- `knowledge`: Access to knowledge base
- `agents`: Access to automation agents
- `data-lake`: Access to data lake
- `user-management`: Access to user management (admin only)

## Backend Setup

### 1. Environment Variables
Create a `.env` file in the backend directory:
```env
DATABASE_URL=postgresql://username:password@localhost/dbname
SECRET_KEY=your-secret-key-here  # Generate with: openssl rand -hex 32
```

### 2. Install Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 3. Database Setup
Run the database migration:
```bash
python scripts/db_setup.py
```

### 4. Create Admin User
Set up the initial admin user:
```bash
python scripts/set_admin_user.py
```

### 5. Run the Backend
```bash
python main.py
# or
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`

## Frontend Setup

### 1. Environment Variables
Create a `.env` file in the frontend directory:
```env
VITE_API_BASE_URL=http://localhost:8000
```

### 2. Install Dependencies
```bash
cd frontend
npm install
```

### 3. Update API Configuration
Ensure `src/api.ts` points to your backend URL.

## Integration Guide

### Backend Integration

1. **Copy the backend module** to your project
2. **Update imports** in `main.py` if your project structure differs
3. **Add the user router** to your existing FastAPI app:
```python
from core.user_routes import router as user_router

app.include_router(
    user_router,
    prefix="/user",
    tags=["User Management"],
    dependencies=[Depends(auth.get_current_active_user)]
)
```

4. **Add authentication endpoints**:
```python
@app.post("/signup", response_model=Token)
def signup(user_data: UserCreate, db: Session = Depends(get_db)):
    # Implementation provided in main.py

@app.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # Implementation provided in main.py
```

### Frontend Integration

1. **Copy the frontend components** to your React project
2. **Wrap your app with AuthProvider**:
```tsx
import { AuthProvider } from './context/AuthContext';

function App() {
  return (
    <AuthProvider>
      {/* Your app components */}
    </AuthProvider>
  );
}
```

3. **Use ProtectedRoute for secured pages**:
```tsx
import { ProtectedRoute } from './components/ProtectedRoute';

<Route path="/admin" element={
  <ProtectedRoute requireAdmin={true}>
    <AdminDashboard />
  </ProtectedRoute>
} />

<Route path="/feature" element={
  <ProtectedRoute requiredPermission="feature-name">
    <FeaturePage />
  </ProtectedRoute>
} />
```

4. **Access user info in components**:
```tsx
import { useAuth } from './context/AuthContext';

function MyComponent() {
  const { userProfile, isAuthenticated } = useAuth();
  
  // Check permissions
  const hasPermission = userProfile?.permissions?.['module-name'] === true;
  const isAdmin = userProfile?.role === 'admin';
}
```

## API Endpoints

### Authentication
- `POST /signup` - Register new user
- `POST /login` - User login
- `GET /debug/my-permissions` - Check current user permissions

### User Management
- `GET /user/profile` - Get current user profile
- `PUT /user/profile` - Update current user profile
- `GET /user/users` - Get all users (admin only)
- `GET /user/users/{user_id}` - Get specific user (admin only)
- `PUT /user/users/{user_id}/permissions` - Update user permissions (admin only)
- `PUT /user/users/{user_id}/toggle-active` - Toggle user active status (admin only)
- `PUT /user/users/{user_id}/profile` - Update user profile (admin only)
- `DELETE /user/users/{user_id}` - Delete user (admin only)

## Security Considerations

1. **Change the SECRET_KEY** in production
2. **Restrict CORS origins** to your frontend domain
3. **Use HTTPS** in production
4. **Implement rate limiting** for authentication endpoints
5. **Add password complexity requirements**
6. **Implement session management** and token refresh
7. **Add audit logging** for admin actions

## Customization

### Adding New Permissions
1. Add the permission key to the default permissions in `database.py`
2. Update the MODULES array in `ProfilePage.tsx`
3. Implement permission checks in your components

### Modifying User Fields
1. Update the User model in `database.py`
2. Add migration logic in `db_setup.py`
3. Update the UserResponse model in `user_routes.py`
4. Update the frontend interfaces and forms

## Troubleshooting

### Common Issues

1. **Database connection errors**: Check DATABASE_URL environment variable
2. **CORS errors**: Ensure backend CORS settings match your frontend URL
3. **Permission denied**: Verify user role and permissions in the database
4. **Token errors**: Check SECRET_KEY consistency between deployments

### Debug Tips

- Use `/debug/my-permissions` endpoint to check current user permissions
- Check browser console for API errors
- Verify database schema matches the models
- Ensure all environment variables are set correctly 