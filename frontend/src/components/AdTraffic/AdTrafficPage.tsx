import React, { useState, useEffect } from 'react';
import {
  Box, Flex, Text, Heading, Button, Card, Grid,
  Dialog, TextField, TextArea, Select, Badge, IconButton
} from '@radix-ui/themes';
import {
  PlusIcon, Pencil1Icon, TrashIcon, LinkBreak1Icon,
  InstagramLogoIcon, VideoIcon, CalendarIcon
} from '@radix-ui/react-icons';
import api from '../../api';

interface Client {
  id: string;
  name: string;
  company_name?: string;
  email?: string;
  phone?: string;
  website?: string;
  industry?: string;
  description?: string;
  facebook_page_name?: string;
  instagram_username?: string;
  auto_post_enabled: boolean;
  created_at: string;
}

export const AdTrafficPage: React.FC = () => {
  const [clients, setClients] = useState<Client[]>([]);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [selectedClient, setSelectedClient] = useState<Client | null>(null);
  const [loading, setLoading] = useState(true);
  
  // Form state
  const [formData, setFormData] = useState({
    name: '',
    company_name: '',
    email: '',
    phone: '',
    website: '',
    industry: '',
    description: '',
    brand_voice: '',
    target_audience: ''
  });

  useEffect(() => {
    fetchClients();
  }, []);

  const fetchClients = async () => {
    try {
      const response = await api.get('/api/ad-traffic/clients');
      setClients(response.data);
    } catch (error) {
      console.error('Failed to fetch clients:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateClient = async () => {
    try {
      const response = await api.post('/api/ad-traffic/clients', formData);
      setClients([response.data, ...clients]);
      setShowCreateDialog(false);
      resetForm();
    } catch (error) {
      console.error('Failed to create client:', error);
    }
  };

  const handleDeleteClient = async (clientId: string) => {
    if (!window.confirm('Are you sure you want to delete this client?')) return;
    
    try {
      await api.delete(`/api/ad-traffic/clients/${clientId}`);
      setClients(clients.filter(c => c.id !== clientId));
    } catch (error) {
      console.error('Failed to delete client:', error);
    }
  };

  const resetForm = () => {
    setFormData({
      name: '',
      company_name: '',
      email: '',
      phone: '',
      website: '',
      industry: '',
      description: '',
      brand_voice: '',
      target_audience: ''
    });
  };

  const navigateToVideoClips = (clientId: string) => {
    // Navigate to video clips with client context
    window.location.href = `/agents?module=video-clip-extractor&clientId=${clientId}`;
  };

  const navigateToCampaigns = (clientId: string) => {
    // Navigate to campaigns with client context
    window.location.href = `/campaigns?clientId=${clientId}`;
  };

  return (
    <Box style={{ height: '100%', padding: '2rem' }}>
      <Flex justify="between" align="center" mb="4">
        <Box>
          <Heading size="7">Ad Traffic</Heading>
          <Text color="gray" size="3">Manage your clients and their social media campaigns</Text>
        </Box>
        <Button onClick={() => setShowCreateDialog(true)}>
          <PlusIcon />
          Add Client
        </Button>
      </Flex>

      {loading ? (
        <Text>Loading clients...</Text>
      ) : clients.length === 0 ? (
        <Card>
          <Flex direction="column" align="center" gap="3" py="5">
            <Text size="3" color="gray">No clients yet</Text>
            <Text size="2" color="gray">Create your first client to get started</Text>
            <Button onClick={() => setShowCreateDialog(true)}>
              <PlusIcon />
              Create Client
            </Button>
          </Flex>
        </Card>
      ) : (
        <Grid columns="repeat(auto-fill, minmax(350px, 1fr))" gap="4">
          {clients.map(client => (
            <Card key={client.id}>
              <Flex direction="column" gap="3">
                <Flex justify="between" align="start">
                  <Box>
                    <Heading size="4">{client.name}</Heading>
                    {client.company_name && (
                      <Text size="2" color="gray">{client.company_name}</Text>
                    )}
                  </Box>
                  <Flex gap="2">
                    <IconButton 
                      size="1" 
                      variant="ghost"
                      onClick={() => handleDeleteClient(client.id)}
                    >
                      <TrashIcon />
                    </IconButton>
                  </Flex>
                </Flex>

                <Box>
                  {client.email && (
                    <Text size="2" as="div" mb="1">📧 {client.email}</Text>
                  )}
                  {client.phone && (
                    <Text size="2" as="div" mb="1">📱 {client.phone}</Text>
                  )}
                  {client.website && (
                    <Text size="2" as="div" mb="1">🌐 {client.website}</Text>
                  )}
                </Box>

                <Flex gap="2" wrap="wrap">
                  {client.facebook_page_name && (
                    <Badge size="1" color="blue">
                      Facebook: {client.facebook_page_name}
                    </Badge>
                  )}
                  {client.instagram_username && (
                    <Badge size="1" color="purple">
                      <InstagramLogoIcon />
                      {client.instagram_username}
                    </Badge>
                  )}
                </Flex>

                <Flex gap="2" mt="2">
                  <Button 
                    size="2" 
                    variant="soft"
                    onClick={() => navigateToVideoClips(client.id)}
                  >
                    <VideoIcon />
                    Video Clips
                  </Button>
                  <Button 
                    size="2" 
                    variant="soft"
                    onClick={() => navigateToCampaigns(client.id)}
                  >
                    <CalendarIcon />
                    Campaigns
                  </Button>
                </Flex>
              </Flex>
            </Card>
          ))}
        </Grid>
      )}

      {/* Create Client Dialog */}
      <Dialog.Root open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <Dialog.Content style={{ maxWidth: 450 }}>
          <Dialog.Title>Create New Client</Dialog.Title>
          
          <Flex direction="column" gap="3">
            <Box>
              <Text as="label" size="2" weight="bold">
                Name *
              </Text>
              <TextField.Root
                placeholder="Client name"
                value={formData.name}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setFormData({...formData, name: e.target.value})}
              />
            </Box>

            <Box>
              <Text as="label" size="2" weight="bold">
                Company
              </Text>
              <TextField.Root
                placeholder="Company name"
                value={formData.company_name}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setFormData({...formData, company_name: e.target.value})}
              />
            </Box>

            <Box>
              <Text as="label" size="2" weight="bold">
                Email
              </Text>
              <TextField.Root
                type="email"
                placeholder="client@example.com"
                value={formData.email}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setFormData({...formData, email: e.target.value})}
              />
            </Box>

            <Box>
              <Text as="label" size="2" weight="bold">
                Phone
              </Text>
              <TextField.Root
                placeholder="+1 (555) 123-4567"
                value={formData.phone}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setFormData({...formData, phone: e.target.value})}
              />
            </Box>

            <Box>
              <Text as="label" size="2" weight="bold">
                Website
              </Text>
              <TextField.Root
                placeholder="https://example.com"
                value={formData.website}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setFormData({...formData, website: e.target.value})}
              />
            </Box>

            <Box>
              <Text as="label" size="2" weight="bold">
                Industry
              </Text>
              <Select.Root value={formData.industry} onValueChange={(value) => setFormData({...formData, industry: value})}>
                <Select.Trigger placeholder="Select industry" />
                <Select.Content>
                  <Select.Item value="real-estate">Real Estate</Select.Item>
                  <Select.Item value="finance">Finance</Select.Item>
                  <Select.Item value="healthcare">Healthcare</Select.Item>
                  <Select.Item value="technology">Technology</Select.Item>
                  <Select.Item value="retail">Retail</Select.Item>
                  <Select.Item value="other">Other</Select.Item>
                </Select.Content>
              </Select.Root>
            </Box>

            <Box>
              <Text as="label" size="2" weight="bold">
                Description
              </Text>
              <TextArea
                placeholder="Brief description of the client..."
                value={formData.description}
                onChange={(e) => setFormData({...formData, description: e.target.value})}
                rows={3}
              />
            </Box>
          </Flex>

          <Flex gap="3" mt="4" justify="end">
            <Dialog.Close>
              <Button variant="soft" color="gray">
                Cancel
              </Button>
            </Dialog.Close>
            <Button onClick={handleCreateClient} disabled={!formData.name}>
              Create Client
            </Button>
          </Flex>
        </Dialog.Content>
      </Dialog.Root>
    </Box>
  );
}; 