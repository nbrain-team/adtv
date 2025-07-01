import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import HomePage from './pages/HomePage';
import KnowledgeBase from './pages/KnowledgeBase';
import HistoryPage from './pages/HistoryPage';
import LoginPage from './pages/LoginPage';
import SignupPage from './pages/SignupPage';
import { MainLayout } from './components/MainLayout';
import { useState } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import LandingPage from './pages/LandingPage';
import AgentsPage from './pages/AgentsPage';
import DataLakePage from './pages/DataLakePage';

// Define the structure for a message
interface Message {
  text: string;
  sender: 'user' | 'ai';
  sources?: (string | { source: string })[];
}

// Create a client
const queryClient = new QueryClient();

// A wrapper for routes that require authentication
const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  const { isAuthenticated, isLoading } = useAuth();
  if (isLoading) {
    return <div>Loading...</div>; // Or a spinner
  }
  return isAuthenticated ? <>{children}</> : <Navigate to="/login" />;
};

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </QueryClientProvider>
  );
}

function AppRoutes() {
  const [messages, setMessages] = useState<Message[]>([]);
  const { isAuthenticated } = useAuth();
  // Forcing a new build with a dummy comment
  return (
    <Router>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/signup" element={<SignupPage />} />

        {/* New home page without sidebar */}
        <Route path="/home" element={
            <ProtectedRoute>
                <LandingPage />
            </ProtectedRoute>
        } />
        
        {/* All other authenticated routes get the sidebar via MainLayout */}
        <Route path="/*" element={
          isAuthenticated ? (
            <MainLayout onNewChat={() => setMessages([])}>
              <Routes>
                <Route path="/" element={<HomePage messages={messages} setMessages={setMessages} />} />
                <Route path="/knowledge" element={<KnowledgeBase />} />
                <Route path="/agents" element={<AgentsPage />} />
                <Route path="/history" element={<HistoryPage />} />
                <Route path="/data-lake" element={<DataLakePage />} />
                {/* Redirect any other nested path to the chat page */}
                <Route path="*" element={<Navigate to="/" />} />
              </Routes>
            </MainLayout>
          ) : <Navigate to="/login" />
        }/>
      </Routes>
    </Router>
  );
}

export default App; 