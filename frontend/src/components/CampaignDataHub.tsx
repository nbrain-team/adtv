import React from 'react';
import { useState, useEffect } from 'react';
import { 
    Box, Flex, Heading, Text, Card, TextField, Badge, Table, 
    Select, Button, ScrollArea, Tabs
} from '@radix-ui/themes';
import { 
    MagnifyingGlassIcon, DownloadIcon, 
    BarChartIcon, PersonIcon, GlobeIcon
} from '@radix-ui/react-icons';
import { MapContainer, TileLayer, CircleMarker, Popup, Marker } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import api from '../api';

// Fix for default markers in react-leaflet
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
    iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
    iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
    shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png'
});

interface Contact {
    id: string;
    campaign_id: string;
    campaign_name?: string;
    first_name?: string;
    last_name?: string;
    email?: string;
    phone?: string;
    company?: string;
    title?: string;
    neighborhood?: string;
    enriched_company?: string;
    enriched_title?: string;
    enriched_phone?: string;
    enriched_linkedin?: string;
    enrichment_status: string;
    created_at: string;
}

interface CampaignSummary {
    id: string;
    name: string;
    total_contacts: number;
}

// Neighborhood coordinates (same as in CampaignDetailPage)
const NEIGHBORHOOD_COORDS: Record<string, [number, number]> = {
    // Alabama cities
    'Madison': [34.6993, -86.7483],
    'Moontown': [34.9037, -86.5303],
    'Monrovia': [34.7915, -86.4831],
    'Huntsville': [34.7304, -86.5861],
    'Birmingham': [33.5186, -86.8104],
    'Montgomery': [32.3668, -86.3000],
    'Mobile': [30.6954, -88.0399],
    'Tuscaloosa': [33.2098, -87.5692],
    'Auburn': [32.6099, -85.4808],
    'Decatur': [34.6059, -86.9833],
    'Florence': [34.7998, -87.6773],
    'Dothan': [31.2232, -85.3905],
    'Hoover': [33.4054, -86.8114],
    'Vestavia Hills': [33.4488, -86.7877],
    'Prattville': [32.4640, -86.4597],
    'Opelika': [32.6454, -85.3783],
    'Enterprise': [31.3152, -85.8552],
    'Northport': [33.2290, -87.5772],
    'Anniston': [33.6598, -85.8316],
    'Phenix City': [32.4710, -85.0008],
    // Additional neighborhoods
    'Research Park': [34.7243, -86.6389],
    'Research Park, Huntsville': [34.7243, -86.6389],
    'Weatherly Heights': [34.7304, -86.5861],
    'Weatherly Heights, Huntsville': [34.7304, -86.5861],
    'Meridianville': [34.8515, -86.5722],
    'New Market': [34.9062, -86.4269],
    'Ryland': [34.8098, -86.4633],
};

const getNeighborhoodCoords = (neighborhood?: string): [number, number] | null => {
    if (!neighborhood) return null;
    
    const cityName = neighborhood.split(',')[0].trim();
    
    if (NEIGHBORHOOD_COORDS[neighborhood]) {
        return NEIGHBORHOOD_COORDS[neighborhood];
    }
    
    if (NEIGHBORHOOD_COORDS[cityName]) {
        return NEIGHBORHOOD_COORDS[cityName];
    }
    
    const lowerNeighborhood = neighborhood.toLowerCase();
    for (const [key, coords] of Object.entries(NEIGHBORHOOD_COORDS)) {
        if (key.toLowerCase() === lowerNeighborhood) {
            return coords;
        }
    }
    
    const lowerCityName = cityName.toLowerCase();
    for (const [key, coords] of Object.entries(NEIGHBORHOOD_COORDS)) {
        if (key.toLowerCase() === lowerCityName) {
            return coords;
        }
    }
    
    return null;
};

export const CampaignDataHub = () => {
    const [contacts, setContacts] = useState<Contact[]>([]);
    const [campaigns, setCampaigns] = useState<CampaignSummary[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState('');
    const [selectedCampaign, setSelectedCampaign] = useState<string>('all');
    const [selectedNeighborhood, setSelectedNeighborhood] = useState<string>('all');
    const [activeTab, setActiveTab] = useState('table');

    useEffect(() => {
        fetchAllData();
    }, []);

    const fetchAllData = async () => {
        try {
            setIsLoading(true);
            
            // Fetch all campaigns for the dropdown
            const campaignsResponse = await api.get('/api/campaigns');
            const campaignsData = campaignsResponse.data;
            setCampaigns(campaignsData);

            // Fetch all contacts in one request
            const contactsResponse = await api.get('/api/campaigns/all-contacts');
            setContacts(contactsResponse.data);
            
        } catch (err) {
            console.error('Failed to fetch data:', err);
        } finally {
            setIsLoading(false);
        }
    };

    const filteredContacts = contacts.filter(contact => {
        const matchesSearch = !searchTerm || 
            Object.values(contact).some(value => 
                value?.toString().toLowerCase().includes(searchTerm.toLowerCase())
            );
        
        const matchesCampaign = selectedCampaign === 'all' || contact.campaign_id === selectedCampaign;
        const matchesNeighborhood = selectedNeighborhood === 'all' || contact.neighborhood === selectedNeighborhood;
        
        return matchesSearch && matchesCampaign && matchesNeighborhood;
    });

    // Get unique neighborhoods
    const neighborhoods = Array.from(new Set(contacts.map(c => c.neighborhood).filter(Boolean))).sort();

    // Calculate neighborhood counts for filtered contacts
    const neighborhoodCounts = filteredContacts.reduce((acc, contact) => {
        if (contact.neighborhood) {
            acc[contact.neighborhood] = (acc[contact.neighborhood] || 0) + 1;
        }
        return acc;
    }, {} as Record<string, number>);

    // Export filtered data
    const handleExport = () => {
        const csvContent = [
            // Headers
            ['First Name', 'Last Name', 'Email', 'Phone', 'Company', 'Title', 'Neighborhood', 'Campaign', 'Status'].join(','),
            // Data rows
            ...filteredContacts.map(contact => [
                contact.first_name || '',
                contact.last_name || '',
                contact.email || '',
                contact.enriched_phone || contact.phone || '',
                contact.enriched_company || contact.company || '',
                contact.enriched_title || contact.title || '',
                contact.neighborhood || '',
                contact.campaign_name || '',
                contact.enrichment_status || ''
            ].map(field => `"${field}"`).join(','))
        ].join('\n');

        const blob = new Blob([csvContent], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `campaign_contacts_${new Date().toISOString().split('T')[0]}.csv`;
        a.click();
    };

    return (
        <Card style={{ marginTop: '2rem' }}>
            <Flex align="center" justify="between" mb="4">
                <Box>
                    <Heading size="5">Campaign Data Hub</Heading>
                    <Text size="2" color="gray">
                        {contacts.length} total contacts across {campaigns.length} campaigns
                    </Text>
                </Box>
                <Button onClick={handleExport} variant="soft">
                    <DownloadIcon />
                    Export Data
                </Button>
            </Flex>

            {/* Filters */}
            <Flex gap="3" mb="4" wrap="wrap">
                <Box style={{ flex: 1, minWidth: '200px' }}>
                    <TextField.Root
                        placeholder="Search all fields..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                    >
                        <TextField.Slot>
                            <MagnifyingGlassIcon />
                        </TextField.Slot>
                    </TextField.Root>
                </Box>
                
                <Select.Root value={selectedCampaign} onValueChange={setSelectedCampaign}>
                    <Select.Trigger placeholder="Filter by campaign..." style={{ minWidth: '200px' }} />
                    <Select.Content>
                        <Select.Item value="all">All Campaigns</Select.Item>
                        <Select.Separator />
                        {campaigns.map(campaign => (
                            <Select.Item key={campaign.id} value={campaign.id}>
                                {campaign.name} ({campaign.total_contacts})
                            </Select.Item>
                        ))}
                    </Select.Content>
                </Select.Root>

                <Select.Root value={selectedNeighborhood} onValueChange={setSelectedNeighborhood}>
                    <Select.Trigger placeholder="Filter by neighborhood..." style={{ minWidth: '200px' }} />
                    <Select.Content>
                        <Select.Item value="all">All Neighborhoods</Select.Item>
                        <Select.Separator />
                        {neighborhoods.map(neighborhood => (
                            <Select.Item key={neighborhood} value={neighborhood || ''}>
                                {neighborhood}
                            </Select.Item>
                        ))}
                    </Select.Content>
                </Select.Root>
            </Flex>

            {/* Summary Stats */}
            <Flex gap="3" mb="4">
                <Badge size="2" color="blue">
                    <PersonIcon />
                    {filteredContacts.length} Contacts
                </Badge>
                <Badge size="2" color="green">
                    {filteredContacts.filter(c => c.email).length} with Email
                </Badge>
                <Badge size="2" color="orange">
                    {filteredContacts.filter(c => c.enriched_phone || c.phone).length} with Phone
                </Badge>
                <Badge size="2" color="purple">
                    {Object.keys(neighborhoodCounts).length} Neighborhoods
                </Badge>
            </Flex>

            {/* Tabs for Table/Map View */}
            <Tabs.Root value={activeTab} onValueChange={setActiveTab}>
                <Tabs.List>
                    <Tabs.Trigger value="table">
                        <BarChartIcon style={{ marginRight: '8px' }} />
                        Table View
                    </Tabs.Trigger>
                    <Tabs.Trigger value="map">
                        <GlobeIcon style={{ marginRight: '8px' }} />
                        Map View
                    </Tabs.Trigger>
                </Tabs.List>

                <Box mt="4">
                    <Tabs.Content value="table">
                        <ScrollArea style={{ height: '400px' }}>
                            <Table.Root>
                                <Table.Header>
                                    <Table.Row>
                                        <Table.ColumnHeaderCell>Name</Table.ColumnHeaderCell>
                                        <Table.ColumnHeaderCell>Email</Table.ColumnHeaderCell>
                                        <Table.ColumnHeaderCell>Phone</Table.ColumnHeaderCell>
                                        <Table.ColumnHeaderCell>Company</Table.ColumnHeaderCell>
                                        <Table.ColumnHeaderCell>Neighborhood</Table.ColumnHeaderCell>
                                        <Table.ColumnHeaderCell>Campaign</Table.ColumnHeaderCell>
                                        <Table.ColumnHeaderCell>Status</Table.ColumnHeaderCell>
                                    </Table.Row>
                                </Table.Header>
                                <Table.Body>
                                    {filteredContacts.slice(0, 100).map(contact => (
                                        <Table.Row key={contact.id}>
                                            <Table.Cell>
                                                {contact.first_name} {contact.last_name}
                                            </Table.Cell>
                                            <Table.Cell>{contact.email || '-'}</Table.Cell>
                                            <Table.Cell>{contact.enriched_phone || contact.phone || '-'}</Table.Cell>
                                            <Table.Cell>{contact.enriched_company || contact.company || '-'}</Table.Cell>
                                            <Table.Cell>{contact.neighborhood || '-'}</Table.Cell>
                                            <Table.Cell>
                                                <Badge size="1" variant="soft">
                                                    {contact.campaign_name}
                                                </Badge>
                                            </Table.Cell>
                                            <Table.Cell>
                                                <Badge 
                                                    size="1"
                                                    color={contact.enrichment_status === 'success' ? 'green' : 'gray'}
                                                >
                                                    {contact.enrichment_status}
                                                </Badge>
                                            </Table.Cell>
                                        </Table.Row>
                                    ))}
                                </Table.Body>
                            </Table.Root>
                            {filteredContacts.length > 100 && (
                                <Text size="2" color="gray" style={{ display: 'block', textAlign: 'center', padding: '1rem' }}>
                                    Showing first 100 of {filteredContacts.length} contacts
                                </Text>
                            )}
                        </ScrollArea>
                    </Tabs.Content>

                    <Tabs.Content value="map">
                        <Box style={{ height: '500px', position: 'relative' }}>
                            {Object.keys(neighborhoodCounts).length === 0 ? (
                                <Flex align="center" justify="center" style={{ height: '100%', backgroundColor: 'var(--gray-2)', borderRadius: '8px' }}>
                                    <Text color="gray">No contacts with valid location data</Text>
                                </Flex>
                            ) : (
                                <MapContainer
                                    center={[33.5186, -86.8104]} // Alabama center
                                    zoom={7}
                                    style={{ height: '100%', width: '100%', borderRadius: '8px' }}
                                >
                                    <TileLayer
                                        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                                        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                                    />
                                    
                                    {Object.entries(neighborhoodCounts).map(([neighborhood, count]) => {
                                        const coords = getNeighborhoodCoords(neighborhood);
                                        if (!coords) return null;
                                        
                                        return (
                                            <CircleMarker
                                                key={neighborhood}
                                                center={coords}
                                                radius={Math.min(30, 10 + Math.sqrt(count) * 3)}
                                                fillColor="#3b82f6"
                                                fillOpacity={0.6}
                                                stroke={true}
                                                color="#1e40af"
                                                weight={2}
                                            >
                                                <Popup>
                                                    <Box>
                                                        <Text weight="bold">{neighborhood}</Text>
                                                        <br />
                                                        <Text>{count} contacts</Text>
                                                    </Box>
                                                </Popup>
                                            </CircleMarker>
                                        );
                                    })}
                                </MapContainer>
                            )}
                        </Box>
                    </Tabs.Content>
                </Box>
            </Tabs.Root>
        </Card>
    );
}; 