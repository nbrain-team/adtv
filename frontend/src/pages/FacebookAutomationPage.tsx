import { useState, useEffect } from 'react';
import { Box, Flex, Text, Heading, Card, Button, Badge, Tabs, Grid, Dialog, IconButton } from '@radix-ui/themes';
import { PlusIcon } from '@radix-ui/react-icons';
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
  const [selectedClient, setSelectedClient] = useState<string | null>('all');
  const [loading, setLoading] = useState(true);
  const [showConnectDialog, setShowConnectDialog] = useState(false);
  const [activeTab, setActiveTab] = useState('dashboard');
  const [dashboardStats, setDashboardStats] = useState({
    totalClients: 0,
    activeCampaigns: 0,
    totalSpend: 0,
    avgRoas: 0
  });

  useEffect(() => {
    fetchClients();
    if (selectedClient === 'all') {
      fetchAllClientsStats();
    }
  }, []);

  useEffect(() => {
    if (selectedClient === 'all') {
      fetchAllClientsStats();
    }
  }, [selectedClient]);

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
      
      // Set initial selected client
      if (clientsData.length > 0 && selectedClient === 'all') {
        // Keep "all" as default
      }
    } catch (error) {
      console.error('Failed to fetch clients:', error);
      setClients([]);
    } finally {
      setLoading(false);
    }
  };

  const fetchAllClientsStats = async () => {
    try {
      // Fetch campaigns for all clients
      const campaignsResponse = await api.get('/facebook-automation/campaigns');
      const campaigns = Array.isArray(campaignsResponse.data) ? campaignsResponse.data : [];
      
      // Calculate stats
      const activeCampaigns = campaigns.filter(c => c.status === 'active').length;
      const totalSpend = campaigns.reduce((sum, c) => sum + (c.spend || 0), 0);
      const avgRoas = campaigns.length > 0 
        ? campaigns.reduce((sum, c) => sum + (c.roas || 0), 0) / campaigns.length 
        : 0;
      
      setDashboardStats({
        totalClients: clients.length,
        activeCampaigns,
        totalSpend,
        avgRoas
      });
    } catch (error) {
      console.error('Failed to fetch stats:', error);
    }
  };

  const handleClientConnected = () => {
    setShowConnectDialog(false);
    fetchClients();
  };

  const handleAddClient = () => {
    setShowConnectDialog(true);
  };

  const getSelectedClientName = () => {
    if (selectedClient === 'all') return 'All Clients';
    const client = clients.find(c => c.id === selectedClient);
    return client?.page_name || 'Select Client';
  };

  if (loading) {
    return (
      <MainLayout onNewChat={() => navigate('/home')}>
        <Box p="6">
          <Card>
            <Flex direction="column" align="center" p="8">
              <Text size="3">Loading dashboard...</Text>
            </Flex>
          </Card>
        </Box>
      </MainLayout>
    );
  }

  return (
    <MainLayout onNewChat={() => navigate('/home')}>
      <Box p="6">
        <Flex justify="between" align="center" mb="6">
          <Box>
            <Heading size="8" mb="2">Facebook Post-to-Ad Automation</Heading>
            <Text color="gray">Transform your realtor social media posts into high-performing ads</Text>
          </Box>
          <Button onClick={handleAddClient} size="3">
            <PlusIcon />
            Add New Client
          </Button>
        </Flex>

        {/* Client Selector with "All Clients" option */}
        <Card mb="4">
          <Flex align="center" gap="4" p="4">
            <Text weight="bold">View:</Text>
            <Flex gap="2" style={{ flex: 1 }}>
              <Button
                variant={selectedClient === 'all' ? 'solid' : 'outline'}
                size="2"
                onClick={() => setSelectedClient('all')}
              >
                All Clients
              </Button>
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
              {selectedClient !== 'all' && clients.find(c => c.id === selectedClient) && 
                `Last sync: ${new Date(clients.find(c => c.id === selectedClient)?.last_sync || '').toLocaleDateString()}`
              }
            </Text>
          </Flex>
        </Card>

        {/* Main Content Tabs */}
        <Tabs.Root value={activeTab} onValueChange={setActiveTab}>
          <Tabs.List size="2">
            <Tabs.Trigger value="dashboard">Dashboard</Tabs.Trigger>
            <Tabs.Trigger value="posts">Posts</Tabs.Trigger>
            <Tabs.Trigger value="campaigns">Campaigns</Tabs.Trigger>
            <Tabs.Trigger value="analytics">Analytics</Tabs.Trigger>
            {selectedClient !== 'all' && (
              <Tabs.Trigger value="settings">Settings</Tabs.Trigger>
            )}
          </Tabs.List>

          <Box mt="4">
            <Tabs.Content value="dashboard">
              {/* Overview Cards */}
              <Grid columns="4" gap="4" mb="6">
                <Card>
                  <Box p="4">
                    <Text size="2" color="gray">Total Clients</Text>
                    <Heading size="7">{clients.length}</Heading>
                  </Box>
                </Card>
                <Card>
                  <Box p="4">
                    <Text size="2" color="gray">Active Campaigns</Text>
                    <Heading size="7">{dashboardStats.activeCampaigns}</Heading>
                  </Box>
                </Card>
                <Card>
                  <Box p="4">
                    <Text size="2" color="gray">Total Spend</Text>
                    <Heading size="7">${dashboardStats.totalSpend.toFixed(0)}</Heading>
                  </Box>
                </Card>
                <Card>
                  <Box p="4">
                    <Text size="2" color="gray">Avg ROAS</Text>
                    <Heading size="7">{dashboardStats.avgRoas.toFixed(1)}x</Heading>
                  </Box>
                </Card>
              </Grid>

              {/* Client Cards Grid */}
              <Heading size="6" mb="4">
                {selectedClient === 'all' ? 'All Connected Pages' : 'Client Overview'}
              </Heading>
              <Grid columns="3" gap="4">
                {(selectedClient === 'all' ? clients : clients.filter(c => c.id === selectedClient)).map(client => (
                  <Card 
                    key={client.id}
                    style={{ cursor: 'pointer' }}
                    onClick={() => {
                      if (selectedClient === 'all') {
                        setSelectedClient(client.id);
                        setActiveTab('posts');
                      }
                    }}
                  >
                    <Box p="4">
                      <Flex justify="between" align="start" mb="3">
                        <Box>
                          <Heading size="5">{client.page_name}</Heading>
                          <Text size="2" color="gray">
                            Budget: ${client.default_daily_budget}/day
                          </Text>
                        </Box>
                        <Badge color={client.is_active ? 'green' : 'gray'}>
                          {client.is_active ? 'Active' : 'Inactive'}
                        </Badge>
                      </Flex>
                      
                      <Grid columns="2" gap="2" mb="3">
                        <Box>
                          <Text size="1" color="gray">Posts</Text>
                          <Text size="3" weight="bold">15</Text>
                        </Box>
                        <Box>
                          <Text size="1" color="gray">Campaigns</Text>
                          <Text size="3" weight="bold">8</Text>
                        </Box>
                      </Grid>

                      <Flex gap="2" mb="2">
                        <Badge variant="soft" color="blue">
                          CTR: 2.3%
                        </Badge>
                        <Badge variant="soft" color="green">
                          ROAS: 3.2x
                        </Badge>
                      </Flex>

                      <Text size="1" color="gray">
                        Last sync: {new Date(client.last_sync || '').toLocaleDateString()}
                      </Text>
                      
                      {client.auto_convert_posts && (
                        <Badge color="orange" size="1" mt="2">
                          Auto-convert enabled
                        </Badge>
                      )}
                    </Box>
                  </Card>
                ))}
              </Grid>

              {/* Recent Activity - only show for "all clients" view */}
              {selectedClient === 'all' && (
                <>
                  <Heading size="6" mt="6" mb="4">Recent Activity</Heading>
                  <Card>
                    <Box p="4">
                      <Flex direction="column" gap="3">
                        <Flex justify="between" align="center">
                          <Flex gap="2" align="center">
                            <Badge color="green">New Post</Badge>
                            <Text size="2">
                              "JUST LISTED! Stunning 4BR/3BA..." imported from Sarah Johnson
                            </Text>
                          </Flex>
                          <Text size="1" color="gray">2 hours ago</Text>
                        </Flex>
                        <Flex justify="between" align="center">
                          <Flex gap="2" align="center">
                            <Badge color="blue">Campaign Started</Badge>
                            <Text size="2">
                              "Spring Home Buyers Campaign #1" launched
                            </Text>
                          </Flex>
                          <Text size="1" color="gray">5 hours ago</Text>
                        </Flex>
                        <Flex justify="between" align="center">
                          <Flex gap="2" align="center">
                            <Badge color="orange">Auto-Convert</Badge>
                            <Text size="2">
                              Post converted to ad for The Davis Team
                            </Text>
                          </Flex>
                          <Text size="1" color="gray">1 day ago</Text>
                        </Flex>
                      </Flex>
                    </Box>
                  </Card>
                </>
              )}
            </Tabs.Content>

            <Tabs.Content value="posts">
              {selectedClient === 'all' ? (
                <Card>
                  <Box p="6" style={{ textAlign: 'center' }}>
                    <Text size="3" color="gray">Please select a specific client to view posts</Text>
                  </Box>
                </Card>
              ) : (
                <FacebookPostsGrid clientId={selectedClient} />
              )}
            </Tabs.Content>

            <Tabs.Content value="campaigns">
              <FacebookCampaignsGrid clientId={selectedClient === 'all' ? null : selectedClient} />
            </Tabs.Content>

            <Tabs.Content value="analytics">
              {selectedClient === 'all' ? (
                <Card>
                  <Box p="6" style={{ textAlign: 'center' }}>
                    <Text size="3" color="gray">Please select a specific client to view detailed analytics</Text>
                  </Box>
                </Card>
              ) : (
                <FacebookAnalyticsDashboard clientId={selectedClient} />
              )}
            </Tabs.Content>

            {selectedClient !== 'all' && (
              <Tabs.Content value="settings">
                <FacebookAutomationSettings 
                  clientId={selectedClient}
                  onUpdate={fetchClients}
                />
              </Tabs.Content>
            )}
          </Box>
        </Tabs.Root>

        {/* Connect Dialog */}
        <Dialog.Root open={showConnectDialog} onOpenChange={setShowConnectDialog}>
          <Dialog.Content maxWidth="500px">
            <FacebookConnectFlow onComplete={handleClientConnected} />
          </Dialog.Content>
        </Dialog.Root>
      </Box>
    </MainLayout>
  );
};

export default FacebookAutomationPage; 