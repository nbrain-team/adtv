import React, { useState, useEffect } from 'react';
import { Box, Flex, Text, TextField, TextArea, Button, Heading } from '@radix-ui/themes';
import { Client, ClientFormData } from './types';
import { api } from '../../services/api';

interface ClientFormProps {
  client: Client | null;
  onSave: () => void;
  onCancel: () => void;
}

export const ClientForm: React.FC<ClientFormProps> = ({
  client,
  onSave,
  onCancel
}) => {
  const [formData, setFormData] = useState<ClientFormData>({
    name: '',
    company_name: '',
    email: '',
    phone: '',
    website: '',
    industry: '',
    description: '',
    brand_voice: '',
    target_audience: '',
    brand_colors: [],
    logo_url: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (client) {
      setFormData({
        name: client.name,
        company_name: client.company_name || '',
        email: client.email || '',
        phone: client.phone || '',
        website: client.website || '',
        industry: client.industry || '',
        description: client.description || '',
        brand_voice: client.brand_voice || '',
        target_audience: client.target_audience || '',
        brand_colors: client.brand_colors || [],
        logo_url: client.logo_url || ''
      });
    }
  }, [client]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      if (client) {
        await api.put(`/api/ad-traffic/clients/${client.id}`, formData);
      } else {
        await api.post('/api/ad-traffic/clients', formData);
      }
      onSave();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to save client');
    } finally {
      setLoading(false);
    }
  };

  const handleColorChange = (colors: string) => {
    const colorArray = colors.split(',').map(c => c.trim()).filter(c => c);
    setFormData({ ...formData, brand_colors: colorArray });
  };

  return (
    <Box>
      <Heading size="5" mb="4">
        {client ? 'Edit Client' : 'Create New Client'}
      </Heading>

      <form onSubmit={handleSubmit}>
        <Flex direction="column" gap="4">
          <Box>
            <Text as="label" size="2" weight="medium" htmlFor="name">Client Name *</Text>
            <TextField.Root
              id="name"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              placeholder="John Doe"
              required
            />
          </Box>

          <Box>
            <Text as="label" size="2" weight="medium" htmlFor="company">Company Name</Text>
            <TextField.Root
              id="company"
              value={formData.company_name}
              onChange={(e) => setFormData({ ...formData, company_name: e.target.value })}
              placeholder="Acme Corp"
            />
          </Box>

          <Flex gap="4">
            <Box style={{ flex: 1 }}>
              <Text as="label" size="2" weight="medium" htmlFor="email">Email</Text>
              <TextField.Root
                id="email"
                type="email"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                placeholder="john@example.com"
              />
            </Box>

            <Box style={{ flex: 1 }}>
              <Text as="label" size="2" weight="medium" htmlFor="phone">Phone</Text>
              <TextField.Root
                id="phone"
                type="tel"
                value={formData.phone}
                onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                placeholder="+1 (555) 123-4567"
              />
            </Box>
          </Flex>

          <Flex gap="4">
            <Box style={{ flex: 1 }}>
              <Text as="label" size="2" weight="medium" htmlFor="website">Website</Text>
              <TextField.Root
                id="website"
                type="url"
                value={formData.website}
                onChange={(e) => setFormData({ ...formData, website: e.target.value })}
                placeholder="https://example.com"
              />
            </Box>

            <Box style={{ flex: 1 }}>
              <Text as="label" size="2" weight="medium" htmlFor="industry">Industry</Text>
              <TextField.Root
                id="industry"
                value={formData.industry}
                onChange={(e) => setFormData({ ...formData, industry: e.target.value })}
                placeholder="Technology, Healthcare, etc."
              />
            </Box>
          </Flex>

          <Box>
            <Text as="label" size="2" weight="medium" htmlFor="description">Description</Text>
            <TextArea
              id="description"
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              placeholder="Brief description of the client..."
              rows={3}
            />
          </Box>

          <Box>
            <Text as="label" size="2" weight="medium" htmlFor="brand_voice">Brand Voice</Text>
            <TextArea
              id="brand_voice"
              value={formData.brand_voice}
              onChange={(e) => setFormData({ ...formData, brand_voice: e.target.value })}
              placeholder="Professional, casual, friendly, authoritative..."
              rows={2}
            />
          </Box>

          <Box>
            <Text as="label" size="2" weight="medium" htmlFor="target_audience">Target Audience</Text>
            <TextArea
              id="target_audience"
              value={formData.target_audience}
              onChange={(e) => setFormData({ ...formData, target_audience: e.target.value })}
              placeholder="Demographics, interests, pain points..."
              rows={2}
            />
          </Box>

          <Box>
            <Text as="label" size="2" weight="medium" htmlFor="brand_colors">Brand Colors</Text>
            <TextField.Root
              id="brand_colors"
              value={formData.brand_colors?.join(', ') || ''}
              onChange={(e) => handleColorChange(e.target.value)}
              placeholder="#1877f2, #42b883, #ff6b6b"
            />
            <Text size="1" color="gray">Comma-separated hex color codes</Text>
          </Box>

          <Box>
            <Text as="label" size="2" weight="medium" htmlFor="logo_url">Logo URL</Text>
            <TextField.Root
              id="logo_url"
              type="url"
              value={formData.logo_url}
              onChange={(e) => setFormData({ ...formData, logo_url: e.target.value })}
              placeholder="https://example.com/logo.png"
            />
          </Box>

          {error && (
            <Text size="2" color="red">{error}</Text>
          )}

          <Flex gap="3" justify="end">
            <Button 
              type="button" 
              variant="soft" 
              onClick={onCancel}
              disabled={loading}
            >
              Cancel
            </Button>
            <Button 
              type="submit" 
              disabled={loading || !formData.name}
            >
              {loading ? 'Saving...' : (client ? 'Update' : 'Create')} Client
            </Button>
          </Flex>
        </Flex>
      </form>
    </Box>
  );
}; 