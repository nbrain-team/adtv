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
import { ProtectedRoute } from './components/ProtectedRoute';
import LandingPage from './pages/LandingPage';
import AgentsPage from './pages/AgentsPage';
import DataLakePage from './pages/DataLakePage';
import ProfilePage from './pages/ProfilePage';
import UserManagementPage from './pages/UserManagementPage';

// Define the structure for a message
interface Message {
  text: string;
  sender: 'user' | 'ai';
  sources?: (string | { source: string })[];
}

// Create a client
const queryClient = new QueryClient();

function App() {
  const [messages, setMessages] = useState<Message[]>([]);

  return (
    <AuthProvider>
      <QueryClientProvider client={queryClient}>
        <Router>
          <Routes>
            <Route path="/" element={<Navigate to="/login" />} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="/signup" element={<SignupPage />} />
            <Route path="/landing" element={
              <ProtectedRoute>
                <LandingPage />
              </ProtectedRoute>
            } />
            <Route path="/home" element={
              <ProtectedRoute requiredPermission="chat">
                <HomePage messages={messages} setMessages={setMessages} />
              </ProtectedRoute>
            } />
            <Route path="/history" element={
              <ProtectedRoute requiredPermission="history">
                <HistoryPage />
              </ProtectedRoute>
            } />
            <Route path="/knowledge" element={
              <ProtectedRoute requiredPermission="knowledge">
                <KnowledgeBase />
              </ProtectedRoute>
            } />
            <Route path="/agents" element={
              <ProtectedRoute requiredPermission="agents">
                <AgentsPage />
              </ProtectedRoute>
            } />
            <Route path="/data-lake" element={
              <ProtectedRoute requiredPermission="data-lake">
                <DataLakePage />
              </ProtectedRoute>
            } />
            <Route path="/profile" element={
              <ProtectedRoute>
                <ProfilePage />
              </ProtectedRoute>
            } />
            <Route path="/user-management" element={
              <ProtectedRoute requireAdmin>
                <UserManagementPage />
              </ProtectedRoute>
            } />
          </Routes>
        </Router>
      </QueryClientProvider>
    </AuthProvider>
  );
}

export default App; 