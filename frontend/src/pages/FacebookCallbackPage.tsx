import { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Box, Text, Card, Flex, Heading } from '@radix-ui/themes';
import { MainLayout } from '../components/MainLayout';
import api from '../api';

const FacebookCallbackPage = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [status, setStatus] = useState<'processing' | 'success' | 'error'>('processing');
  const [errorMessage, setErrorMessage] = useState('');

  useEffect(() => {
    handleCallback();
  }, []);

  const handleCallback = async () => {
    const code = searchParams.get('code');
    const state = searchParams.get('state');
    const error = searchParams.get('error');
    const errorDescription = searchParams.get('error_description');

    if (error) {
      setStatus('error');
      setErrorMessage(errorDescription || 'Facebook authorization was denied');
      return;
    }

    if (!code || !state) {
      setStatus('error');
      setErrorMessage('Invalid callback parameters');
      return;
    }

    try {
      await api.post('/facebook-automation/facebook/callback', {
        code,
        state
      });

      setStatus('success');
      
      // Add a success message for mock mode
      if (code === 'mock_auth_code') {
        console.log('Mock mode: Successfully connected mock Facebook account');
      }
      
      // Redirect to Facebook automation page after success
      setTimeout(() => {
        navigate('/facebook-automation');
      }, 2000);
    } catch (error: any) {
      setStatus('error');
      setErrorMessage(error.response?.data?.detail || 'Failed to connect Facebook account');
    }
  };

  return (
    <MainLayout onNewChat={() => navigate('/home')}>
      <Box p="6">
        <Card style={{ maxWidth: 500, margin: '0 auto' }}>
          <Box p="6" style={{ textAlign: 'center' }}>
            {status === 'processing' && (
              <>
                <Heading size="6" mb="3">Connecting to Facebook...</Heading>
                <Text color="gray">Please wait while we complete the authorization</Text>
              </>
            )}

            {status === 'success' && (
              <>
                <Heading size="6" mb="3" color="green">Successfully Connected!</Heading>
                <Text color="gray">Redirecting you to the Facebook automation dashboard...</Text>
              </>
            )}

            {status === 'error' && (
              <>
                <Heading size="6" mb="3" color="red">Connection Failed</Heading>
                <Text color="gray" mb="4">{errorMessage}</Text>
                <button 
                  onClick={() => navigate('/facebook-automation')}
                  style={{
                    padding: '8px 16px',
                    backgroundColor: 'var(--accent-9)',
                    color: 'white',
                    border: 'none',
                    borderRadius: 4,
                    cursor: 'pointer'
                  }}
                >
                  Back to Facebook Automation
                </button>
              </>
            )}
          </Box>
        </Card>
      </Box>
    </MainLayout>
  );
};

export default FacebookCallbackPage; 