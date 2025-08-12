import { useState, useEffect } from 'react';
import { Box, Flex, Text, Heading, Card, Button, Badge, Tabs, Grid, Dialog } from '@radix-ui/themes';
import { MainLayout } from '../components/MainLayout';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import FacebookConnectFlow from '../components/FacebookAutomation/FacebookConnectFlow';
import FacebookPostsGrid from '../components/FacebookAutomation/FacebookPostsGrid';
import FacebookCampaignsGrid from '../components/FacebookAutomation/FacebookCampaignsGrid';
import FacebookAnalyticsDashboard from '../components/FacebookAutomation/FacebookAnalyticsDashboard';
import FacebookAutomationSettings from '../components/FacebookAutomation/FacebookAutomationSettings';
import api from '../api';

interface FacebookClient {
  id: string;
  page_name: string;
  is_active: boolean;
  auto_convert_posts: boolean;
  default_daily_budget: number;
  last_sync: string;
}

const FacebookAutomationPage = () => {
  const navigate = useNavigate();
  const { userProfile } = useAuth();
  const [clients, setClients] = useState<FacebookClient[]>([]);
  const [selectedClient, setSelectedClient] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [showConnectDialog, setShowConnectDialog] = useState(false);
  const [activeTab, setActiveTab] = useState('posts');
  const [isMockMode, setIsMockMode] = useState(false);

  useEffect(() => {
    fetchClients();
  }, []);

  const fetchClients = async () => {
    try {
      const response = await api.get('/facebook-automation/clients');
      const clientsData = response.data;
      
      // Ensure we have an array
      if (!Array.isArray(clientsData)) {
        console.error('Expected array of clients, got:', clientsData);
        setClients([]);
        setLoading(false);
        return;
      }
      
      setClients(clientsData);
      
      // Check if we're in mock mode (all clients have mock IDs)
      const mockMode = clientsData.length > 0 && 
        clientsData.every((client: FacebookClient) => 
          client.page_name.includes('Sarah Johnson') || 
          client.page_name.includes('Mike Chen') || 
          client.page_name.includes('Davis Team')
        );
      setIsMockMode(mockMode);
      
      if (clientsData.length > 0 && !selectedClient) {
        setSelectedClient(clientsData[0].id);
      }
    } catch (error) {
      console.error('Failed to fetch clients:', error);
      setClients([]);
    } finally {
      setLoading(false);
    }
  };

  const handleClientConnected = () => {
    setShowConnectDialog(false);
    fetchClients();
  };

  const handleSyncPosts = async (clientId: string) => {
    try {
      await api.post(`/facebook-automation/clients/${clientId}/sync-posts`);
      // Show success toast
    } catch (error) {
      console.error('Failed to sync posts:', error);
    }
  };

  if (!userProfile?.permissions?.['facebook-automation']) {
    // Temporarily disabled for demo - uncomment for production
    /*
    return (
      <MainLayout onNewChat={() => navigate('/home')}>
        <Box p="6">
          <Card>
            <Flex direction="column" align="center" p="6">
              <Text size="3" mb="4">Facebook Automation is not enabled for your account.</Text>
              <Button onClick={() => navigate('/landing')}>Go Back</Button>
            </Flex>
          </Card>
        </Box>
      </MainLayout>
    );
    */
  }

  return (
    <MainLayout onNewChat={() => navigate('/home')}>
      <Box p="6">
        {/* Removed mock mode banner for cleaner demo */}
        
        <Flex justify="between" align="center" mb="6">
          <Box>
            <Heading size="8" mb="2">Facebook Post-to-Ad Automation</Heading>
            <Text color="gray">Transform your realtor social media posts into high-performing ads</Text>
          </Box>
          <Flex gap="3">
            {/* Removed sync posts and connect page buttons for demo */}
          </Flex>
        </Flex>

        {/* Always show the main interface */}
        {loading ? (
          <Card>
            <Flex direction="column" align="center" p="8">
              <Text size="3">Loading dashboard...</Text>
            </Flex>
          </Card>
        ) : (
          <>
            {/* Client Selector */}
            {clients.length > 0 && (
              <Card mb="4">
                <Flex align="center" gap="4" p="4">
                  <Text weight="bold">Active Page:</Text>
                  <Flex gap="2" style={{ flex: 1 }}>
                    {clients.map(client => (
                      <Button
                        key={client.id}
                        variant={selectedClient === client.id ? 'solid' : 'outline'}
                        size="2"
                        onClick={() => setSelectedClient(client.id)}
                      >
                        <Flex align="center" gap="2">
                          <Text>{client.page_name}</Text>
                          {client.auto_convert_posts && (
                            <Badge color="green" size="1">Auto</Badge>
                          )}
                        </Flex>
                      </Button>
                    ))}
                  </Flex>
                  <Text size="2" color="gray">
                    Last sync: {new Date(clients.find(c => c.id === selectedClient)?.last_sync || '').toLocaleDateString()}
                  </Text>
                </Flex>
              </Card>
            )}

            {/* Main Content Tabs */}
            <Tabs.Root value={activeTab} onValueChange={setActiveTab}>
              <Tabs.List size="2">
                <Tabs.Trigger value="posts">Posts</Tabs.Trigger>
                <Tabs.Trigger value="campaigns">Campaigns</Tabs.Trigger>
                <Tabs.Trigger value="analytics">Analytics</Tabs.Trigger>
                <Tabs.Trigger value="settings">Settings</Tabs.Trigger>
              </Tabs.List>

              <Box mt="4">
                <Tabs.Content value="posts">
                  <FacebookPostsGrid clientId={selectedClient} />
                </Tabs.Content>

                <Tabs.Content value="campaigns">
                  <FacebookCampaignsGrid clientId={selectedClient} />
                </Tabs.Content>

                <Tabs.Content value="analytics">
                  <FacebookAnalyticsDashboard clientId={selectedClient} />
                </Tabs.Content>

                <Tabs.Content value="settings">
                  <FacebookAutomationSettings 
                    clientId={selectedClient}
                    onUpdate={fetchClients}
                  />
                </Tabs.Content>
              </Box>
            </Tabs.Root>
          </>
        )}
      </Box>
    </MainLayout>
  );
};

export default FacebookAutomationPage; 