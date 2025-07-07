import { Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

interface ProtectedRouteProps {
  children: React.ReactNode;
  requiredPermission?: string;
  requireAdmin?: boolean;
}

export const ProtectedRoute = ({ children, requiredPermission, requireAdmin }: ProtectedRouteProps) => {
  const { isAuthenticated, isLoading, userProfile } = useAuth();
  
  if (isLoading) {
    return <div>Loading...</div>;
  }
  
  if (!isAuthenticated) {
    return <Navigate to="/login" />;
  }
  
  // Check admin requirement
  if (requireAdmin && userProfile?.role !== 'admin') {
    return <Navigate to="/home" />;
  }
  
  // Check specific permission
  if (requiredPermission && userProfile?.permissions?.[requiredPermission] === false) {
    return <Navigate to="/home" />;
  }
  
  return <>{children}</>;
}; 