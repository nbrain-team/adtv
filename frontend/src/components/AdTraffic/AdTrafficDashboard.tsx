import React, { useState, useEffect } from 'react';
import { Box, Flex, Text, Button, Tabs, Heading, Badge, Progress } from '@radix-ui/themes';
import { PlusIcon, CalendarIcon, PersonIcon, VideoIcon } from '@radix-ui/react-icons';
import { ClientList } from './ClientList';
import { CalendarView } from './CalendarView';
import { ClientForm } from './ClientForm';
import { PostModal } from './PostModal';
import { CampaignModal } from './CampaignModal';
import { ClientSelector } from './ClientSelector';
import { CampaignsList } from './CampaignsList';
import { MainLayout } from '../MainLayout';
import { api } from '../../services/api';
import { Client, SocialPost, Campaign, CampaignStatus } from './types';
import * as Dialog from '@radix-ui/react-dialog';

export const AdTrafficDashboard: React.FC = () => {
  const [activeTab, setActiveTab] = useState('clients');
  const [clients, setClients] = useState<Client[]>([]);
  const [selectedClient, setSelectedClient] = useState<Client | null>(null);
  const [posts, setPosts] = useState<SocialPost[]>([]);
  const [showClientModal, setShowClientModal] = useState(false);
  const [showPostModal, setShowPostModal] = useState(false);
  const [showCampaignModal, setShowCampaignModal] = useState(false);
  const [editingClient, setEditingClient] = useState<Client | null>(null);
  const [activeCampaigns, setActiveCampaigns] = useState<Campaign[]>([]);
  const [loading, setLoading] = useState(true);
  const [viewingCampaign, setViewingCampaign] = useState<Campaign | null>(null);
  
  // Modal states
  const [showClientForm, setShowClientForm] = useState(false);
  const [editingPost, setEditingPost] = useState<SocialPost | null>(null);
  
  // View state
  // const [activeTab, setActiveTab] = useState('calendar'); // This line is removed as per the new_code

  // Fetch clients on mount
  useEffect(() => {
    fetchClients();
  }, []);

  // Fetch posts when client changes
  useEffect(() => {
    if (selectedClient) {
      fetchClientPosts(selectedClient.id);
    }
  }, [selectedClient]);

  const fetchClients = async () => {
    try {
      const response = await api.get('/api/ad-traffic/clients');
      setClients(response.data);
      if (response.data.length > 0 && !selectedClient) {
        setSelectedClient(response.data[0]);
      }
    } catch (error) {
      console.error('Error fetching clients:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchClientPosts = async (clientId: string) => {
    try {
      const response = await api.get(`/api/ad-traffic/clients/${clientId}/calendar`);
      setPosts(response.data);
    } catch (error) {
      console.error('Error fetching posts:', error);
    }
  };

  const handleCreateClient = () => {
    setEditingClient(null);
    setShowClientForm(true);
  };

  const handleEditClient = (client: Client) => {
    setEditingClient(client);
    setShowClientForm(true);
  };

  const handleDeleteClient = async (clientId: string) => {
    if (window.confirm('Are you sure you want to delete this client?')) {
      try {
        await api.delete(`/api/ad-traffic/clients/${clientId}`);
        await fetchClients();
        if (selectedClient?.id === clientId) {
          setSelectedClient(clients[0] || null);
        }
      } catch (error) {
        console.error('Error deleting client:', error);
      }
    }
  };

  const handleClientSaved = async () => {
    await fetchClients();
    setShowClientForm(false);
  };

  const handleCreatePost = () => {
    setEditingPost(null);
    setShowPostModal(true);
  };

  const handleEditPost = (post: SocialPost) => {
    setEditingPost(post);
    setShowPostModal(true);
  };

  const handleDeletePost = async (postId: string) => {
    if (window.confirm('Are you sure you want to delete this post?')) {
      try {
        await api.delete(`/api/ad-traffic/posts/${postId}`);
        if (selectedClient) {
          await fetchClientPosts(selectedClient.id);
        }
      } catch (error) {
        console.error('Error deleting post:', error);
      }
    }
  };

  const handlePostSaved = async () => {
    if (selectedClient) {
      await fetchClientPosts(selectedClient.id);
    }
    setShowPostModal(false);
  };

  const handleCreateCampaign = () => {
    setShowCampaignModal(true);
  };

  const handleCampaignCreated = async (campaign: Campaign) => {
    // Close modal immediately
    setShowCampaignModal(false);
    
    // Add campaign to active campaigns list
    setActiveCampaigns(prev => [...prev, campaign]);
    
    // Start polling for this campaign's status
    pollCampaignStatus(campaign.id);
    
    // Refresh posts if we have a selected client
    if (selectedClient) {
      await fetchClientPosts(selectedClient.id);
    }
  };

  const pollCampaignStatus = (campaignId: string) => {
    const interval = setInterval(async () => {
      try {
        const response = await api.get<Campaign>(`/api/ad-traffic/campaigns/${campaignId}`);
        const updatedCampaign = response.data;
        
        // Update the campaign in our list
        setActiveCampaigns(prev => 
          prev.map(c => c.id === campaignId ? updatedCampaign : c)
        );
        
        // Stop polling if campaign is no longer processing
        if (updatedCampaign.status !== CampaignStatus.PROCESSING) {
          clearInterval(interval);
          
          // Remove from active campaigns after a delay if completed
          if (updatedCampaign.status === CampaignStatus.READY) {
            setTimeout(() => {
              setActiveCampaigns(prev => prev.filter(c => c.id !== campaignId));
            }, 5000);
          }
        }
      } catch (err) {
        console.error('Failed to poll campaign status:', err);
        clearInterval(interval);
      }
    }, 3000);
  };

  const handleViewCampaign = async (campaign: Campaign) => {
    setViewingCampaign(campaign);
    // Fetch campaign posts
    try {
      const response = await api.get(`/api/ad-traffic/campaigns/${campaign.id}/posts`);
      setPosts(response.data);
      setActiveTab('calendar');
    } catch (error) {
      console.error('Error fetching campaign posts:', error);
    }
  };

  const handleBackToAllPosts = () => {
    setViewingCampaign(null);
    if (selectedClient) {
      fetchClientPosts(selectedClient.id);
    }
  };

  return (
    <MainLayout onNewChat={() => {}}>
      <Box style={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
        {/* Header */}
        <Box style={{ 
          padding: '1rem 2rem', 
          borderBottom: '1px solid var(--gray-4)',
          backgroundColor: 'white' 
        }}>
          <Flex justify="between" align="center">
            <Box>
              <Heading size="6">Ad Traffic Manager</Heading>
              <Text size="2" color="gray">
                Manage clients and their social media campaigns
              </Text>
            </Box>
            
            <Flex gap="3" align="center">
              {selectedClient && (
                <ClientSelector
                  clients={clients}
                  selectedClient={selectedClient}
                  onSelectClient={setSelectedClient}
                />
              )}
              
              <Button 
                size="2" 
                onClick={handleCreateClient}
                style={{ cursor: 'pointer' }}
              >
                <PlusIcon /> Add Client
              </Button>
            </Flex>
          </Flex>
        </Box>

        {/* Main Content */}
        <Box style={{ flex: 1, overflow: 'hidden' }}>
          {loading ? (
            <Flex align="center" justify="center" style={{ height: '100%' }}>
              <Text>Loading...</Text>
            </Flex>
          ) : clients.length === 0 ? (
            <Flex 
              direction="column" 
              align="center" 
              justify="center" 
              gap="4"
              style={{ height: '100%' }}
            >
              <PersonIcon width="48" height="48" color="gray" />
              <Text size="4" color="gray">No clients yet</Text>
              <Button onClick={handleCreateClient}>
                <PlusIcon /> Create Your First Client
              </Button>
            </Flex>
          ) : (
            <>
              {/* Active Campaigns Banner */}
              {activeCampaigns.length > 0 && (
                <Box style={{ 
                  padding: '1rem 2rem', 
                  backgroundColor: 'var(--blue-2)',
                  borderBottom: '1px solid var(--blue-6)'
                }}>
                  <Text size="2" weight="medium" style={{ marginBottom: '0.5rem' }}>
                    Active Campaigns
                  </Text>
                  <Flex direction="column" gap="2">
                    {activeCampaigns.map(campaign => (
                      <Flex key={campaign.id} align="center" gap="3">
                        <Text size="2">{campaign.name}</Text>
                        <Badge color={
                          campaign.status === CampaignStatus.PROCESSING ? 'blue' :
                          campaign.status === CampaignStatus.READY ? 'green' : 'red'
                        }>
                          {campaign.status}
                        </Badge>
                        {campaign.status === CampaignStatus.PROCESSING && (
                          <>
                            <Progress value={campaign.progress || 0} style={{ width: '100px' }} />
                            <Text size="1" color="gray">{campaign.progress || 0}%</Text>
                          </>
                        )}
                      </Flex>
                    ))}
                  </Flex>
                </Box>
              )}
              
              <Tabs.Root value={activeTab} onValueChange={setActiveTab}>
                <Tabs.List style={{ padding: '0 2rem' }}>
                  <Tabs.Trigger value="calendar">
                    <CalendarIcon /> Calendar
                  </Tabs.Trigger>
                  <Tabs.Trigger value="campaigns">
                    <VideoIcon /> Campaigns
                  </Tabs.Trigger>
                  <Tabs.Trigger value="clients">
                    <PersonIcon /> Clients
                  </Tabs.Trigger>
                </Tabs.List>

                <Box style={{ height: 'calc(100% - 48px)', overflow: 'auto' }}>
                  <Tabs.Content value="calendar" style={{ height: '100%' }}>
                    {selectedClient && (
                      <>
                        {viewingCampaign && (
                          <Box style={{ 
                            padding: '1rem 2rem', 
                            backgroundColor: 'var(--amber-2)',
                            borderBottom: '1px solid var(--amber-6)'
                          }}>
                            <Flex justify="between" align="center">
                              <Text size="2">
                                Viewing campaign: <strong>{viewingCampaign.name}</strong>
                              </Text>
                              <Button size="2" variant="soft" onClick={handleBackToAllPosts}>
                                Back to All Posts
                              </Button>
                            </Flex>
                          </Box>
                        )}
                        <CalendarView
                          client={selectedClient}
                          posts={posts}
                          onCreatePost={handleCreatePost}
                          onEditPost={handleEditPost}
                          onDeletePost={handleDeletePost}
                          onCreateCampaign={handleCreateCampaign}
                        />
                      </>
                    )}
                  </Tabs.Content>

                  <Tabs.Content value="campaigns" style={{ padding: '2rem' }}>
                    {selectedClient ? (
                      <CampaignsList
                        clientId={selectedClient.id}
                        onViewCampaign={handleViewCampaign}
                        onRefresh={() => selectedClient && fetchClientPosts(selectedClient.id)}
                      />
                    ) : (
                      <Flex align="center" justify="center" style={{ height: '100%' }}>
                        <Text color="gray">Please select a client first</Text>
                      </Flex>
                    )}
                  </Tabs.Content>

                  <Tabs.Content value="clients">
                    <ClientList
                      clients={clients}
                      selectedClient={selectedClient}
                      onSelectClient={setSelectedClient}
                      onEditClient={handleEditClient}
                      onDeleteClient={handleDeleteClient}
                    />
                  </Tabs.Content>
                </Box>
              </Tabs.Root>
            </>
          )}
        </Box>

        {/* Modals */}
        <Dialog.Root open={showClientForm} onOpenChange={setShowClientForm}>
          <Dialog.Content style={{ maxWidth: '500px' }}>
            <ClientForm
              client={editingClient}
              onSave={handleClientSaved}
              onCancel={() => setShowClientForm(false)}
            />
          </Dialog.Content>
        </Dialog.Root>

        <Dialog.Root open={showPostModal} onOpenChange={setShowPostModal}>
          <Dialog.Content style={{ maxWidth: '600px' }}>
            {selectedClient && (
              <PostModal
                client={selectedClient}
                post={editingPost}
                onSave={handlePostSaved}
                onCancel={() => setShowPostModal(false)}
              />
            )}
          </Dialog.Content>
        </Dialog.Root>

        <Dialog.Root open={showCampaignModal} onOpenChange={setShowCampaignModal}>
          <Dialog.Content style={{ maxWidth: '700px' }}>
            <Dialog.Title style={{ display: 'none' }}>Create Video Campaign</Dialog.Title>
            {selectedClient && (
              <CampaignModal
                client={selectedClient}
                onComplete={handleCampaignCreated}
                onCancel={() => setShowCampaignModal(false)}
              />
            )}
          </Dialog.Content>
        </Dialog.Root>
      </Box>
    </MainLayout>
  );
}; 