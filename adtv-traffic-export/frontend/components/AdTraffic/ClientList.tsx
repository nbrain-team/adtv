import React from 'react';
import { Box, Card, Flex, Text, Heading, Button, Avatar, Badge } from '@radix-ui/themes';
import { Pencil2Icon, TrashIcon } from '@radix-ui/react-icons';
import { Client } from './types';

interface ClientListProps {
  clients: Client[];
  selectedClient: Client | null;
  onSelectClient: (client: Client) => void;
  onEditClient: (client: Client) => void;
  onDeleteClient: (clientId: string) => void;
}

export const ClientList: React.FC<ClientListProps> = ({
  clients,
  selectedClient,
  onSelectClient,
  onEditClient,
  onDeleteClient
}) => {
  return (
    <Box style={{ padding: '2rem' }}>
      <Box style={{ 
        display: 'grid', 
        gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))',
        gap: '1rem'
      }}>
        {clients.map(client => (
          <Card
            key={client.id}
            style={{
              cursor: 'pointer',
              border: selectedClient?.id === client.id ? '2px solid var(--accent-9)' : '1px solid var(--gray-4)',
              transition: 'all 0.2s'
            }}
            onClick={() => onSelectClient(client)}
          >
            <Flex direction="column" gap="3">
              <Flex justify="between" align="start">
                <Flex gap="3" align="center">
                  <Avatar
                    size="3"
                    fallback={client.name.charAt(0).toUpperCase()}
                    color="indigo"
                  />
                  <Box>
                    <Heading size="3">{client.name}</Heading>
                    {client.company_name && (
                      <Text size="2" color="gray">{client.company_name}</Text>
                    )}
                  </Box>
                </Flex>
                
                <Flex gap="2">
                  <Button
                    size="1"
                    variant="ghost"
                    onClick={(e) => {
                      e.stopPropagation();
                      onEditClient(client);
                    }}
                  >
                    <Pencil2Icon />
                  </Button>
                  <Button
                    size="1"
                    variant="ghost"
                    color="red"
                    onClick={(e) => {
                      e.stopPropagation();
                      onDeleteClient(client.id);
                    }}
                  >
                    <TrashIcon />
                  </Button>
                </Flex>
              </Flex>

              <Flex gap="2" wrap="wrap">
                {client.email && (
                  <Badge size="1" variant="soft">
                    <Text size="1">{client.email}</Text>
                  </Badge>
                )}
                {client.phone && (
                  <Badge size="1" variant="soft">
                    <Text size="1">{client.phone}</Text>
                  </Badge>
                )}
                {client.industry && (
                  <Badge size="1" variant="soft" color="blue">
                    <Text size="1">{client.industry}</Text>
                  </Badge>
                )}
              </Flex>

              {client.description && (
                <Text size="2" color="gray" style={{ 
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  display: '-webkit-box',
                  WebkitLineClamp: 2,
                  WebkitBoxOrient: 'vertical'
                }}>
                  {client.description}
                </Text>
              )}

              <Flex gap="2" justify="between" align="center">
                <Text size="1" color="gray">
                  Created {new Date(client.created_at).toLocaleDateString()}
                </Text>
                {Object.keys(client.social_accounts || {}).length > 0 && (
                  <Badge size="1" color="green">
                    {Object.keys(client.social_accounts).length} accounts connected
                  </Badge>
                )}
              </Flex>
            </Flex>
          </Card>
        ))}
      </Box>
    </Box>
  );
}; 