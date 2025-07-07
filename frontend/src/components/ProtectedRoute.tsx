import { Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { MainLayout } from './MainLayout';
import { Box, Heading, Text, Button } from '@radix-ui/themes';
import { useNavigate } from 'react-router-dom';

interface ProtectedRouteProps {
  children: React.ReactNode;
  requiredPermission?: string;
  requireAdmin?: boolean;
}

export const ProtectedRoute = ({ children, requiredPermission, requireAdmin }: ProtectedRouteProps) => {
  const { isAuthenticated, isLoading, userProfile } = useAuth();
  const navigate = useNavigate();
  
  if (isLoading) {
    return <div>Loading...</div>;
  }
  
  if (!isAuthenticated) {
    return <Navigate to="/login" />;
  }
  
  // Check admin requirement
  if (requireAdmin && userProfile?.role !== 'admin') {
    return (
      <MainLayout onNewChat={() => navigate('/home')}>
        <Box style={{ 
          height: '100vh', 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'center',
          flexDirection: 'column',
          gap: '1rem'
        }}>
          <Heading size="6">Access Denied</Heading>
          <Text>You need administrator privileges to access this page.</Text>
          <Button onClick={() => navigate('/home')}>Go to Home</Button>
        </Box>
      </MainLayout>
    );
  }
  
  // Check specific permission
  if (requiredPermission && userProfile?.permissions?.[requiredPermission] !== true) {
    return (
      <MainLayout onNewChat={() => navigate('/home')}>
        <Box style={{ 
          height: '100vh', 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'center',
          flexDirection: 'column',
          gap: '1rem'
        }}>
          <Heading size="6">Access Denied</Heading>
          <Text>You don't have permission to access this module.</Text>
          <Button onClick={() => navigate('/home')}>Go to Home</Button>
        </Box>
      </MainLayout>
    );
  }
  
  return <>{children}</>;
}; 