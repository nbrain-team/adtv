import React, { useState, useEffect } from 'react';
import { Box, Tabs, Spinner, Flex, Heading, Button, Dialog, AlertDialog, Text } from '@radix-ui/themes';
import { PlusIcon, PersonIcon, CalendarIcon, VideoIcon } from '@radix-ui/react-icons';
import { ClientList } from './ClientList';
import { ClientForm } from './ClientForm';
import { ClientDetailView } from './ClientDetailView';
import { Client, SocialPost, Campaign } from './types';
import { api } from '../../services/api';

export const AdTrafficDashboard: React.FC = () => {
  const [clients, setClients] = useState<Client[]>([]);
  const [selectedClient, setSelectedClient] = useState<Client | null>(null);
  const [showClientModal, setShowClientModal] = useState(false);
  const [editingClient, setEditingClient] = useState<Client | null>(null);
  const [loading, setLoading] = useState(true);
  const [showClientDetail, setShowClientDetail] = useState(false);
  
  // Modal states
  const [showClientForm, setShowClientForm] = useState(false);

  // Fetch clients on mount
  useEffect(() => {
    fetchClients();
  }, []);

  const fetchClients = async () => {
    try {
      const response = await api.get('/api/ad-traffic/clients');
      setClients(response.data);
    } catch (error) {
      console.error('Error fetching clients:', error);
    } finally {
      setLoading(false);
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
    try {
      await api.delete(`/api/ad-traffic/clients/${clientId}`);
      await fetchClients();
      if (selectedClient?.id === clientId) {
        setSelectedClient(null);
        setShowClientDetail(false);
      }
    } catch (error) {
      console.error('Error deleting client:', error);
    }
  };

  const handleSelectClient = (client: Client) => {
    setSelectedClient(client);
    setShowClientDetail(true);
  };

  const handleClientUpdate = async () => {
    await fetchClients();
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
          
          <Button onClick={handleCreateClient} variant="outline">
            <PersonIcon />
            New Client
          </Button>
        </Flex>
      </Box>

      {/* Main Content */}
      <Box style={{ flex: 1, overflow: 'hidden' }}>
        {showClientDetail && selectedClient ? (
          <ClientDetailView 
            client={selectedClient}
            onBack={() => setShowClientDetail(false)}
            onClientUpdate={handleClientUpdate}
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
    </Box>
  );
}; 