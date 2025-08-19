import { useState, useEffect } from 'react';
import { Box, Flex, Text, Heading, Card, Button, Badge, Dialog, Select } from '@radix-ui/themes';
import { PlusIcon, CalendarIcon } from '@radix-ui/react-icons';
import { MainLayout } from '../components/MainLayout';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
// import { useAuth } from '../context/AuthContext';
import FacebookConnectFlow from '../components/FacebookAutomation/FacebookConnectFlow';
import FacebookVisualCalendar from '../components/FacebookAutomation/FacebookVisualCalendar';
import FacebookCampaignCards from '../components/FacebookAutomation/FacebookCampaignCards';
import FacebookPostsGrid from '../components/FacebookAutomation/FacebookPostsGrid';
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
  ad_account_id?: string;
  facebook_page_id?: string;
}

const FacebookAutomationPage = () => {
  const navigate = useNavigate();
  const { isAuthenticated, isLoading } = useAuth();
  const [clients, setClients] = useState<FacebookClient[]>([]);
  const [selectedClient, setSelectedClient] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [showConnectDialog, setShowConnectDialog] = useState(false);
  const [activeView, setActiveView] = useState<'calendar' | 'posts' | 'ads' | 'analytics' | 'settings'>('calendar');
  const [syncing, setSyncing] = useState(false);
  const [dateRange, setDateRange] = useState({
    start: new Date(),
    end: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000)
  });

  useEffect(() => {
    if (!isLoading && isAuthenticated) {
      fetchClients();
    }
  }, [isLoading, isAuthenticated]);

  const fetchClients = async () => {
    try {
      const ONLY_PAGE_ID = (import.meta as any).env?.VITE_ONLY_FACEBOOK_PAGE_ID as string | undefined;
      const ONLY_AD_ACCOUNT_ID = (import.meta as any).env?.VITE_ONLY_FACEBOOK_AD_ACCOUNT_ID as string | undefined;
      const paramsPrimary: Record<string, string> = {};
      if (ONLY_PAGE_ID) paramsPrimary.page_id = ONLY_PAGE_ID;
      if (ONLY_AD_ACCOUNT_ID) paramsPrimary.ad_account_id = ONLY_AD_ACCOUNT_ID;
      const response = await api.get('/api/facebook-automation/clients', { params: paramsPrimary });
      const clientsData = response.data;
      
      if (!Array.isArray(clientsData)) {
        console.error('Expected array of clients, got:', clientsData);
        setClients([]);
        setLoading(false);
        return;
      }
      
      // If no client exists yet but env targets are set, try to connect automatically
      if (clientsData.length === 0 && ONLY_PAGE_ID && ONLY_AD_ACCOUNT_ID) {
        try {
          await api.post('/api/facebook-automation/facebook/manual-connect', {
            page_id: ONLY_PAGE_ID,
            ad_account_id: ONLY_AD_ACCOUNT_ID,
            page_name: undefined
          });
          // Refetch with page filter only to avoid excluding if ad account differs
          const refetch = await api.get('/api/facebook-automation/clients', { params: { page_id: ONLY_PAGE_ID } });
          setClients(refetch.data || []);
          if (Array.isArray(refetch.data) && refetch.data.length > 0 && !selectedClient) {
            setSelectedClient(refetch.data[0].id);
          }
        } catch (e) {
          console.error('Auto-connect failed:', e);
          setClients([]);
        }
      } else {
        // If primary query returned nothing but ad_account filter was applied, retry with page filter only
        if (clientsData.length === 0 && ONLY_PAGE_ID && ONLY_AD_ACCOUNT_ID) {
          const fallback = await api.get('/api/facebook-automation/clients', { params: { page_id: ONLY_PAGE_ID } });
          setClients(Array.isArray(fallback.data) ? fallback.data : []);
        } else {
          setClients(clientsData);
        }
      }
      
      // Auto-select first (and only) client if none selected
      if (clientsData.length > 0 && !selectedClient) setSelectedClient(clientsData[0].id);
    } catch (error: any) {
      console.error('Failed to fetch clients:', error);
      if (error?.response?.status === 401) {
        navigate('/login');
        return;
      }
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

  if (loading || isLoading) {
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
                <Select.Trigger style={{ minWidth: 260 }}>
                  <Flex align="center" gap="2">
                    {getSelectedClientData()?.page_profile_pic && (
                      <img 
                        src={getSelectedClientData()?.page_profile_pic} 
                        alt="" 
                        style={{ width: 20, height: 20, borderRadius: '50%' }}
                      />
                    )}
                    <Text>
                      {getSelectedClientData()?.page_name || 'Select Page'}
                      {getSelectedClientData()?.ad_account_id ? ` (${getSelectedClientData()?.ad_account_id.replace('act_', '')})` : ''}
                    </Text>
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
                        <Text>
                          {client.page_name}
                          {client.ad_account_id ? ` (${client.ad_account_id.replace('act_', '')})` : ''}
                        </Text>
                        {client.is_active && <Badge color="green" size="1">Active</Badge>}
                      </Flex>
                    </Select.Item>
                  ))}
                </Select.Content>
              </Select.Root>
            </Flex>

            <Flex align="center" gap="4">
              {/* View Toggles */}
              <Flex gap="4" style={{ 
                background: 'var(--gray-3)', 
                padding: '8px 10px',
                borderRadius: 12 
              }}>
                <Button 
                  size="3" 
                  variant={activeView === 'calendar' ? 'solid' : 'ghost'}
                  onClick={() => setActiveView('calendar')}
                >
                  <CalendarIcon />
                  Calendar
                </Button>
                <Button 
                  size="3" 
                  variant={activeView === 'posts' ? 'solid' : 'ghost'}
                  onClick={() => setActiveView('posts')}
                >
                  Posts
                </Button>
                <Button 
                  size="3" 
                  variant={activeView === 'ads' ? 'solid' : 'ghost'}
                  onClick={() => setActiveView('ads')}
                >
                  Ads
                </Button>
                <Button 
                  size="3" 
                  variant={activeView === 'analytics' ? 'solid' : 'ghost'}
                  onClick={() => setActiveView('analytics')}
                >
                  Analytics
                </Button>
                <Button 
                  size="3" 
                  variant={activeView === 'settings' ? 'solid' : 'ghost'}
                  onClick={() => setActiveView('settings')}
                >
                  Settings
                </Button>
              </Flex>
              <Button
                disabled={!selectedClient || syncing}
                variant="soft"
                onClick={async () => {
                  if (!selectedClient) return;
                  try {
                    setSyncing(true);
                    await api.post(`/api/facebook-automation/clients/${selectedClient}/sync-posts`);
                  } catch (e) {
                    console.error('Failed to start sync:', e);
                  } finally {
                    setSyncing(false);
                  }
                }}
              >
                {syncing ? 'Syncing…' : 'Sync Posts'}
              </Button>
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
                  <Text size="3" color="gray" style={{ display: 'block', marginBottom: 16 }}>
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
              
              {activeView === 'posts' && selectedClient && (
                <FacebookPostsGrid clientId={selectedClient} hideConverted={true} />
              )}
              {activeView === 'ads' && selectedClient && (
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
            <Dialog.Title>Connect a Facebook Page</Dialog.Title>
            <FacebookConnectFlow onComplete={handleClientConnected} />
          </Dialog.Content>
        </Dialog.Root>
      </Box>
    </MainLayout>
  );
};

export default FacebookAutomationPage; 