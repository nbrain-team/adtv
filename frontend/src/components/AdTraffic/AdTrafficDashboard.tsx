import React, { useState, useEffect } from 'react';
import { Box, Flex, Heading, Text, Button, Tabs, Dialog } from '@radix-ui/themes';
import { PlusIcon, PersonIcon, CalendarIcon } from '@radix-ui/react-icons';
import { MainLayout } from '../MainLayout';
import { ClientList } from './ClientList';
import { CalendarView } from './CalendarView';
import { ClientForm } from './ClientForm';
import { PostModal } from './PostModal';
import { CampaignModal } from './CampaignModal';
import { ClientSelector } from './ClientSelector';
import { api } from '../../services/api';
import { Client, SocialPost, Campaign } from './types';

export const AdTrafficDashboard: React.FC = () => {
  const [clients, setClients] = useState<Client[]>([]);
  const [selectedClient, setSelectedClient] = useState<Client | null>(null);
  const [posts, setPosts] = useState<SocialPost[]>([]);
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [loading, setLoading] = useState(true);
  
  // Modal states
  const [showClientForm, setShowClientForm] = useState(false);
  const [showPostModal, setShowPostModal] = useState(false);
  const [showCampaignModal, setShowCampaignModal] = useState(false);
  const [editingClient, setEditingClient] = useState<Client | null>(null);
  const [editingPost, setEditingPost] = useState<SocialPost | null>(null);
  
  // View state
  const [activeTab, setActiveTab] = useState('calendar');

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

  const handleCampaignCreated = async () => {
    if (selectedClient) {
      await fetchClientPosts(selectedClient.id);
    }
    setShowCampaignModal(false);
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
            <Tabs.Root value={activeTab} onValueChange={setActiveTab}>
              <Tabs.List style={{ padding: '0 2rem' }}>
                <Tabs.Trigger value="calendar">
                  <CalendarIcon /> Calendar
                </Tabs.Trigger>
                <Tabs.Trigger value="clients">
                  <PersonIcon /> Clients
                </Tabs.Trigger>
              </Tabs.List>

              <Box style={{ height: 'calc(100% - 48px)', overflow: 'auto' }}>
                <Tabs.Content value="calendar" style={{ height: '100%' }}>
                  {selectedClient && (
                    <CalendarView
                      client={selectedClient}
                      posts={posts}
                      onCreatePost={handleCreatePost}
                      onEditPost={handleEditPost}
                      onDeletePost={handleDeletePost}
                      onCreateCampaign={handleCreateCampaign}
                    />
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
          )}
        </Box>

        {/* Modals */}
        <Dialog.Root open={showClientForm} onOpenChange={setShowClientForm}>
          <Dialog.Content maxWidth="500px">
            <ClientForm
              client={editingClient}
              onSave={handleClientSaved}
              onCancel={() => setShowClientForm(false)}
            />
          </Dialog.Content>
        </Dialog.Root>

        <Dialog.Root open={showPostModal} onOpenChange={setShowPostModal}>
          <Dialog.Content maxWidth="600px">
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
          <Dialog.Content maxWidth="700px">
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