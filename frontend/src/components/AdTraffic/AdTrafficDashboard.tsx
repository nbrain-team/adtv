import React, { useState, useEffect } from 'react';
import { Box, Tabs, Spinner, Flex, Heading, Button, Dialog, AlertDialog, Text } from '@radix-ui/themes';
import { PlusIcon, PersonIcon, CalendarIcon, VideoIcon } from '@radix-ui/react-icons';
import { ClientList } from './ClientList';
import { ClientForm } from './ClientForm';
import { ClientDetailView } from './ClientDetailView';
import { CalendarView } from './CalendarView';
import { PostModal } from './PostModal';
import { CampaignModal } from './CampaignModal';
import { Client, SocialPost, Campaign } from './types';
import { api } from '../../services/api';

export const AdTrafficDashboard: React.FC = () => {
  const [activeTab, setActiveTab] = useState('calendar');
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
  const [showClientDetail, setShowClientDetail] = useState(false);
  
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
    if (selectedClient && !showClientDetail) {
      fetchClientPosts(selectedClient.id);
    }
  }, [selectedClient, showClientDetail]);

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

  const handleClientSaved = async (client: Client) => {
    await fetchClients();
    setShowClientForm(false);
    setEditingClient(null);
    setSelectedClient(client);
  };

  const handleDeleteClient = async (clientId: string) => {
    try {
      await api.delete(`/api/ad-traffic/clients/${clientId}`);
      await fetchClients();
      if (selectedClient?.id === clientId) {
        setSelectedClient(clients[0] || null);
      }
    } catch (error) {
      console.error('Error deleting client:', error);
    }
  };

  const handleSelectClient = (client: Client) => {
    setSelectedClient(client);
    if (activeTab === 'clients') {
      setShowClientDetail(true);
    }
  };

  const handleCreatePost = () => {
    setEditingPost(null);
    setShowPostModal(true);
  };

  const handleEditPost = (post: SocialPost) => {
    setEditingPost(post);
    setShowPostModal(true);
  };

  const handlePostSaved = async () => {
    if (selectedClient) {
      await fetchClientPosts(selectedClient.id);
    }
    setShowPostModal(false);
    setEditingPost(null);
  };

  const handleDeletePost = async (postId: string) => {
    try {
      await api.delete(`/api/ad-traffic/posts/${postId}`);
      if (selectedClient) {
        await fetchClientPosts(selectedClient.id);
      }
    } catch (error) {
      console.error('Error deleting post:', error);
    }
  };

  const handleCreateCampaign = () => {
    setShowCampaignModal(true);
  };

  const handleCampaignCreated = async (campaign: Campaign) => {
    setShowCampaignModal(false);
    // Show the campaign view
    setViewingCampaign(campaign);
    setActiveTab('campaign');
    
    // Refresh campaigns
    if (selectedClient) {
      const response = await api.get(`/api/ad-traffic/clients/${selectedClient.id}/campaigns`);
      setActiveCampaigns(response.data);
    }
  };

  const handleCampaignClose = () => {
    setViewingCampaign(null);
    setActiveTab('calendar');
  };

  if (loading) {
    return (
      <Box style={{ padding: '2rem' }}>
        <Flex align="center" justify="center" style={{ minHeight: '400px' }}>
          <Spinner size="3" />
        </Flex>
      </Box>
    );
  }

  return (
    <Box style={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <Box style={{ 
        padding: '1.5rem 2rem', 
        borderBottom: '1px solid var(--gray-4)',
        backgroundColor: 'white'
      }}>
        <Flex align="center" justify="between">
          <Box>
            <Heading size="7" style={{ color: 'var(--gray-12)' }}>
              Ad Traffic Manager
            </Heading>
            <Text size="2" color="gray" style={{ marginTop: '0.25rem' }}>
              Manage your social media campaigns and content
            </Text>
          </Box>
          
          <Flex gap="3">
            {selectedClient && (
              <>
                <Button onClick={handleCreatePost}>
                  <PlusIcon />
                  New Post
                </Button>
                <Button onClick={handleCreateCampaign} variant="soft">
                  <VideoIcon />
                  New Campaign
                </Button>
              </>
            )}
            <Button onClick={handleCreateClient} variant="outline">
              <PersonIcon />
              New Client
            </Button>
          </Flex>
        </Flex>
      </Box>

      {/* Main Content */}
      <Box style={{ flex: 1, overflow: 'hidden' }}>
        <Tabs.Root value={activeTab} onValueChange={(value) => {
          setActiveTab(value);
          if (value !== 'clients') {
            setShowClientDetail(false);
          }
        }}>
          <Box style={{ 
            padding: '0 2rem', 
            borderBottom: '1px solid var(--gray-4)',
            backgroundColor: 'white'
          }}>
            <Tabs.List>
              <Tabs.Trigger value="calendar">
                <CalendarIcon style={{ marginRight: '8px' }} />
                Calendar
              </Tabs.Trigger>
              <Tabs.Trigger value="clients">
                <PersonIcon style={{ marginRight: '8px' }} />
                Clients
              </Tabs.Trigger>
            </Tabs.List>
          </Box>

          <Box style={{ height: 'calc(100% - 48px)', overflow: 'auto' }}>
            <Tabs.Content value="calendar" style={{ height: '100%' }}>
              {selectedClient ? (
                <CalendarView
                  client={selectedClient}
                  posts={posts}
                  onCreatePost={handleCreatePost}
                  onEditPost={handleEditPost}
                  onDeletePost={handleDeletePost}
                  onCreateCampaign={handleCreateCampaign}
                />
              ) : (
                <Box style={{ padding: '2rem', textAlign: 'center' }}>
                  <Text color="gray">No client selected. Please create or select a client.</Text>
                </Box>
              )}
            </Tabs.Content>

            <Tabs.Content value="clients" style={{ height: '100%' }}>
              {showClientDetail && selectedClient ? (
                <ClientDetailView 
                  client={selectedClient}
                  onBack={() => setShowClientDetail(false)}
                />
              ) : (
                <ClientList
                  clients={clients}
                  selectedClient={selectedClient}
                  onSelectClient={handleSelectClient}
                  onEditClient={handleEditClient}
                  onDeleteClient={handleDeleteClient}
                />
              )}
            </Tabs.Content>
          </Box>
        </Tabs.Root>
      </Box>

      {/* Modals */}
      <Dialog.Root open={showClientForm} onOpenChange={setShowClientForm}>
        <Dialog.Content style={{ maxWidth: 600 }}>
          <ClientForm
            client={editingClient}
            onSave={async () => {
              await fetchClients();
              setShowClientForm(false);
              setEditingClient(null);
            }}
            onCancel={() => setShowClientForm(false)}
          />
        </Dialog.Content>
      </Dialog.Root>

      <Dialog.Root open={showPostModal} onOpenChange={setShowPostModal}>
        <Dialog.Content style={{ maxWidth: 600 }}>
          {selectedClient && (
            <PostModal
              client={selectedClient}
              post={editingPost}
              onSave={handlePostSaved}
              onCancel={() => setShowPostModal(false)}
              onDelete={editingPost ? handleDeletePost : undefined}
            />
          )}
        </Dialog.Content>
      </Dialog.Root>

      <Dialog.Root open={showCampaignModal} onOpenChange={setShowCampaignModal}>
        <Dialog.Content style={{ maxWidth: 600 }}>
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
  );
}; 