import React from 'react';
import { Select, Text } from '@radix-ui/themes';
import { Client } from './types';

interface ClientSelectorProps {
  clients: Client[];
  selectedClient: Client | null;
  onSelectClient: (client: Client) => void;
}

export const ClientSelector: React.FC<ClientSelectorProps> = ({
  clients,
  selectedClient,
  onSelectClient
}) => {
  const handleChange = (clientId: string) => {
    const client = clients.find(c => c.id === clientId);
    if (client) {
      onSelectClient(client);
    }
  };

  return (
    <Select.Root value={selectedClient?.id || ''} onValueChange={handleChange}>
      <Select.Trigger>
        <Text weight="medium">
          {selectedClient?.name || 'Select a client'}
        </Text>
      </Select.Trigger>
      <Select.Content>
        {clients.map(client => (
          <Select.Item key={client.id} value={client.id}>
            {client.name}
            {client.company_name && (
              <Text size="1" color="gray"> - {client.company_name}</Text>
            )}
          </Select.Item>
        ))}
      </Select.Content>
    </Select.Root>
  );
}; 