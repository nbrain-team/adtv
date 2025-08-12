import { useState } from 'react';
import { Box, Flex, Text, Heading, Button } from '@radix-ui/themes';
import api from '../../api';

interface FacebookConnectFlowProps {
  onComplete: () => void;
}

const FacebookConnectFlow: React.FC<FacebookConnectFlowProps> = ({ onComplete }) => {
  const [loading, setLoading] = useState(false);

  const handleConnect = async () => {
    try {
      setLoading(true);
      
      // Get the redirect URI based on current location
      const redirectUri = `${window.location.origin}/facebook-callback`;
      
      // Get the auth URL from backend
      const response = await api.get('/api/facebook-automation/facebook/auth', {
        params: { redirect_uri: redirectUri }
      });

      // Check if we're in mock mode
      if (response.data.mock_mode) {
        // In mock mode, directly go to the callback URL
        window.location.href = response.data.auth_url;
      } else {
        // Redirect to real Facebook OAuth
        window.location.href = response.data.auth_url;
      }
    } catch (error) {
      console.error('Failed to initiate Facebook auth:', error);
      setLoading(false);
    }
  };

  return (
    <Box>
      <Heading size="6" mb="4">Connect Your Facebook Page</Heading>
      
      <Text size="3" mb="4" color="gray">
        To get started, you'll need to authorize access to your Facebook page and ad account.
      </Text>

      <Box mb="4" p="4" style={{ backgroundColor: 'var(--gray-2)', borderRadius: 8 }}>
        <Text size="2" weight="bold" mb="2">We'll need permission to:</Text>
        <ul style={{ margin: 0, paddingLeft: 20 }}>
          <li><Text size="2">View and manage your Facebook pages</Text></li>
          <li><Text size="2">Create and manage ad campaigns</Text></li>
          <li><Text size="2">Access page insights and post engagement</Text></li>
          <li><Text size="2">Post content on your behalf (optional)</Text></li>
        </ul>
      </Box>

      <Flex gap="3" justify="end">
        <Button variant="outline" onClick={onComplete}>
          Cancel
        </Button>
        <Button 
          onClick={handleConnect} 
          disabled={loading}
          style={{ backgroundColor: '#1877f2' }}
        >
          {loading ? 'Connecting...' : 'Connect with Facebook'}
        </Button>
      </Flex>
    </Box>
  );
};

export default FacebookConnectFlow; 