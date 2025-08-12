import { useState, useEffect } from 'react';
import { Box, Flex, Text, Heading, Card, Button, Badge, Tabs, Grid, Dialog, IconButton, Select, TextField } from '@radix-ui/themes';
import { PlusIcon, CalendarIcon, ChevronLeftIcon, ChevronRightIcon, MagnifyingGlassIcon } from '@radix-ui/react-icons';
import { MainLayout } from '../components/MainLayout';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import FacebookConnectFlow from '../components/FacebookAutomation/FacebookConnectFlow';
import FacebookVisualCalendar from '../components/FacebookAutomation/FacebookVisualCalendar';
import FacebookCampaignCards from '../components/FacebookAutomation/FacebookCampaignCards';
import FacebookAnalyticsOverview from '../components/FacebookAutomation/FacebookAnalyticsOverview';
import FacebookAutomationSettings from '../components/FacebookAutomation/FacebookAutomationSettings';
import api from '../api';

interface FacebookClient {
  id: string;
  page_name: string;
  page_profile_pic?: string;
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
  const [activeView, setActiveView] = useState<'calendar' | 'campaigns' | 'analytics' | 'settings'>('calendar');
  const [searchQuery, setSearchQuery] = useState('');
  const [dateRange, setDateRange] = useState({
    start: new Date(),
    end: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000)
  });

  useEffect(() => {
    fetchClients();
  }, []);

  const fetchClients = async () => {
    try {
      const response = await api.get('/api/facebook-automation/clients');
      const clientsData = response.data;
      
      if (!Array.isArray(clientsData)) {
        console.error('Expected array of clients, got:', clientsData);
        setClients([]);
        setLoading(false);
        return;
      }
      
      setClients(clientsData);
      
      // Auto-select first client if none selected
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

  const getSelectedClientData = () => {
    return clients.find(c => c.id === selectedClient);
  };

  if (loading) {
    return (
      <MainLayout onNewChat={() => navigate('/home')}>
        <Box style={{ 
          minHeight: '100vh', 
          background: 'linear-gradient(to bottom, var(--gray-1), var(--gray-2))'
        }}>
          <Flex align="center" justify="center" style={{ minHeight: '50vh' }}>
            <Card>
              <Box p="6">
                <Text size="3">Loading your social media dashboard...</Text>
              </Box>
            </Card>
          </Flex>
        </Box>
      </MainLayout>
    );
  }

  return (
    <MainLayout onNewChat={() => navigate('/home')}>
      <Box style={{ 
        minHeight: '100vh', 
        background: 'linear-gradient(to bottom, var(--gray-1), var(--gray-2))'
      }}>
        {/* Modern Header */}
        <Box style={{ 
          background: 'white', 
          borderBottom: '1px solid var(--gray-4)',
          position: 'sticky',
          top: 0,
          zIndex: 100
        }}>
          <Flex justify="between" align="center" p="4">
            <Flex align="center" gap="4">
              <Heading size="6">Social Media Hub</Heading>
              
              {/* Client Selector */}
              <Select.Root value={selectedClient || ''} onValueChange={setSelectedClient}>
                <Select.Trigger style={{ minWidth: 200 }}>
                  <Flex align="center" gap="2">
                    {getSelectedClientData()?.page_profile_pic && (
                      <img 
                        src={getSelectedClientData()?.page_profile_pic} 
                        alt="" 
                        style={{ width: 20, height: 20, borderRadius: '50%' }}
                      />
                    )}
                    <Text>{getSelectedClientData()?.page_name || 'Select Page'}</Text>
                  </Flex>
                </Select.Trigger>
                <Select.Content>
                  {clients.map(client => (
                    <Select.Item key={client.id} value={client.id}>
                      <Flex align="center" gap="2">
                        {client.page_profile_pic && (
                          <img 
                            src={client.page_profile_pic} 
                            alt="" 
                            style={{ width: 20, height: 20, borderRadius: '50%' }}
                          />
                        )}
                        <Text>{client.page_name}</Text>
                        {client.is_active && <Badge color="green" size="1">Active</Badge>}
                      </Flex>
                    </Select.Item>
                  ))}
                </Select.Content>
              </Select.Root>
            </Flex>

            <Flex align="center" gap="3">
              {/* Search */}
              <TextField.Root placeholder="Search posts..." style={{ width: 300 }}>
                <TextField.Slot>
                  <MagnifyingGlassIcon height="16" width="16" />
                </TextField.Slot>
              </TextField.Root>

              {/* View Toggles */}
              <Flex gap="1" style={{ 
                background: 'var(--gray-3)', 
                padding: 2,
                borderRadius: 6 
              }}>
                <Button 
                  size="2" 
                  variant={activeView === 'calendar' ? 'solid' : 'ghost'}
                  onClick={() => setActiveView('calendar')}
                >
                  <CalendarIcon />
                  Calendar
                </Button>
                <Button 
                  size="2" 
                  variant={activeView === 'campaigns' ? 'solid' : 'ghost'}
                  onClick={() => setActiveView('campaigns')}
                >
                  Campaigns
                </Button>
                <Button 
                  size="2" 
                  variant={activeView === 'analytics' ? 'solid' : 'ghost'}
                  onClick={() => setActiveView('analytics')}
                >
                  Analytics
                </Button>
                <Button 
                  size="2" 
                  variant={activeView === 'settings' ? 'solid' : 'ghost'}
                  onClick={() => setActiveView('settings')}
                >
                  Settings
                </Button>
              </Flex>

              <Button onClick={() => setShowConnectDialog(true)} size="3">
                <PlusIcon />
                Connect Page
              </Button>
            </Flex>
          </Flex>
        </Box>

        {/* Main Content Area */}
        <Box p="4">
          {clients.length === 0 ? (
            <Flex align="center" justify="center" style={{ minHeight: '60vh' }}>
              <Card style={{ maxWidth: 600, width: '100%' }}>
                <Box p="8" style={{ textAlign: 'center' }}>
                  <Heading size="6" mb="3">Welcome to Your Social Media Hub</Heading>
                  <Text size="3" color="gray" mb="6">
                    Connect your Facebook pages to start automating your social media marketing
                  </Text>
                  <Button size="4" onClick={() => setShowConnectDialog(true)}>
                    <PlusIcon />
                    Connect Your First Page
                  </Button>
                </Box>
              </Card>
            </Flex>
          ) : (
            <>
              {activeView === 'calendar' && selectedClient && (
                <FacebookVisualCalendar 
                  clientId={selectedClient} 
                  dateRange={dateRange}
                  onDateRangeChange={setDateRange}
                />
              )}
              
              {activeView === 'campaigns' && selectedClient && (
                <FacebookCampaignCards clientId={selectedClient} />
              )}
              
              {activeView === 'analytics' && selectedClient && (
                <FacebookAnalyticsOverview clientId={selectedClient} />
              )}
              
              {activeView === 'settings' && selectedClient && (
                <Card>
                  <Box p="6">
                    <FacebookAutomationSettings 
                      clientId={selectedClient}
                      onUpdate={fetchClients}
                    />
                  </Box>
                </Card>
              )}
            </>
          )}
        </Box>

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