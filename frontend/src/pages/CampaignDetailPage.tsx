import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
    Box, Flex, Heading, Text, Card, Button, Badge, Tabs, Table, 
    Checkbox, TextField, TextArea, Callout, IconButton, Dialog,
    DropdownMenu, ScrollArea, Select
} from '@radix-ui/themes';
import { 
    ArrowLeftIcon, UploadIcon, PersonIcon, EnvelopeClosedIcon, 
    BarChartIcon, InfoCircledIcon, MagnifyingGlassIcon, 
    Pencil1Icon, TrashIcon, CheckIcon, Cross2Icon, DotsHorizontalIcon,
    DownloadIcon, ReloadIcon
} from '@radix-ui/react-icons';
import { MainLayout } from '../components/MainLayout';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import api from '../api';
import { MapContainer, TileLayer, CircleMarker, Popup } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';

interface Campaign {
    id: string;
    name: string;
    owner_name: string;
    owner_email: string;
    launch_date: string;
    event_type: 'virtual' | 'in_person';
    event_date: string;
    hotel_name?: string;
    hotel_address?: string;
    calendly_link?: string;
    status: string;
    total_contacts: number;
    enriched_contacts: number;
    failed_enrichments: number;
    emails_generated: number;
    emails_sent: number;
    email_template?: string;
    email_subject?: string;
    created_at: string;
    updated_at: string;
    event_times?: string[];
    target_cities?: string;
}

interface Contact {
    id: string;
    first_name?: string;
    last_name?: string;
    email?: string;
    company?: string;
    title?: string;
    phone?: string;
    neighborhood?: string;
    // Enriched data
    enriched_company?: string;
    enriched_title?: string;
    enriched_phone?: string;
    enriched_linkedin?: string;
    enriched_website?: string;
    enriched_industry?: string;
    enriched_company_size?: string;
    enriched_location?: string;
    // Status
    enrichment_status: string;
    email_status: string;
    excluded: boolean;
    personalized_email?: string;
    personalized_subject?: string;
}

interface EmailTemplate {
    id: string;
    name: string;
    subject: string;
    body: string;
    goal: string;
}

const getStatusColor = (status: string) => {
    const statusColors: Record<string, any> = {
        'draft': 'gray',
        'enriching': 'blue',
        'ready_for_personalization': 'yellow',
        'generating_emails': 'blue',
        'ready_to_send': 'green',
        'sending': 'blue',
        'sent': 'green'
    };
    return statusColors[status] || 'gray';
};

const getStatusLabel = (status: string) => {
    const statusLabels: Record<string, string> = {
        'draft': 'Draft',
        'enriching': 'Enriching Contacts',
        'ready_for_personalization': 'Ready for Personalization',
        'generating_emails': 'Generating Emails',
        'ready_to_send': 'Ready to Send',
        'sending': 'Sending',
        'sent': 'Sent'
    };
    return statusLabels[status] || status;
};

// Neighborhood coordinates for demo - in production, you'd use a geocoding service
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
    // Original San Diego neighborhoods (keep for compatibility)
    'Downtown': [32.7157, -117.1611],
    'La Jolla': [32.8328, -117.2713],
    'Pacific Beach': [32.7944, -117.2356],
    'Mission Valley': [32.7678, -117.1569],
    'Hillcrest': [32.7477, -117.1640],
    'North Park': [32.7403, -117.1290],
    'Coronado': [32.6859, -117.1831],
    'Point Loma': [32.6670, -117.2415],
    'Ocean Beach': [32.7494, -117.2469],
    'Mission Beach': [32.7707, -117.2521],
    // Add more neighborhoods as needed
};

const getNeighborhoodCoords = (neighborhood?: string): [number, number] | null => {
    if (!neighborhood) return null;
    
    // Try exact match first
    if (NEIGHBORHOOD_COORDS[neighborhood]) {
        return NEIGHBORHOOD_COORDS[neighborhood];
    }
    
    // Try case-insensitive match
    const lowerNeighborhood = neighborhood.toLowerCase();
    for (const [key, coords] of Object.entries(NEIGHBORHOOD_COORDS)) {
        if (key.toLowerCase() === lowerNeighborhood) {
            return coords;
        }
    }
    
    return null;
};

const CampaignDetailPage = () => {
    const { campaignId } = useParams<{ campaignId: string }>();
    const navigate = useNavigate();
    const fileInputRef = useRef<HTMLInputElement>(null);
    
    const [campaign, setCampaign] = useState<Campaign | null>(null);
    const [contacts, setContacts] = useState<Contact[]>([]);
    const [selectedContacts, setSelectedContacts] = useState<Set<string>>(new Set());
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [activeTab, setActiveTab] = useState('overview');
    const [searchTerm, setSearchTerm] = useState('');
    const [editingContact, setEditingContact] = useState<string | null>(null);
    const [editingEmail, setEditingEmail] = useState('');
    const [showEmailPreview, setShowEmailPreview] = useState(false);
    const [previewContact, setPreviewContact] = useState<Contact | null>(null);
    const [emailTemplate, setEmailTemplate] = useState('');
    const [emailSubject, setEmailSubject] = useState('');
    const [enrichmentStatus, setEnrichmentStatus] = useState<any>(null);
    const [availableTemplates, setAvailableTemplates] = useState<EmailTemplate[]>([]);
    const [selectedTemplateId, setSelectedTemplateId] = useState<string>('');
    const [isLoadingTemplates, setIsLoadingTemplates] = useState(false);

    useEffect(() => {
        if (campaignId) {
            fetchCampaign();
            fetchContacts();
            fetchTemplates();
        }
    }, [campaignId]);

    useEffect(() => {
        if (campaign?.status === 'enriching') {
            const interval = setInterval(fetchEnrichmentStatus, 5000); // Check every 5 seconds
            fetchEnrichmentStatus(); // Initial fetch
            return () => clearInterval(interval);
        }
    }, [campaign?.status]);

    useEffect(() => {
        if (campaign) {
            setEmailTemplate(campaign.email_template || '');
            setEmailSubject(campaign.email_subject || '');
        }
    }, [campaign]);

    const fetchCampaign = async () => {
        try {
            const response = await api.get(`/api/campaigns/${campaignId}`);
            setCampaign(response.data);
        } catch (err) {
            setError('Failed to load campaign');
        } finally {
            setIsLoading(false);
        }
    };

    const fetchContacts = async () => {
        try {
            const response = await api.get(`/api/campaigns/${campaignId}/contacts`);
            setContacts(response.data);
        } catch (err) {
            console.error('Failed to load contacts:', err);
        }
    };

    const fetchEnrichmentStatus = async () => {
        try {
            const response = await api.get(`/api/campaigns/${campaignId}/enrichment-status`);
            setEnrichmentStatus(response.data);
            
            // If enrichment is complete, refresh the campaign
            if (response.data.progress_percentage === 100) {
                fetchCampaign();
            }
        } catch (err) {
            console.error('Failed to fetch enrichment status:', err);
        }
    };

    const fetchTemplates = async () => {
        setIsLoadingTemplates(true);
        try {
            const response = await api.get('/api/email-templates');
            setAvailableTemplates(response.data);
        } catch (err) {
            console.error('Failed to fetch templates:', err);
        } finally {
            setIsLoadingTemplates(false);
        }
    };

    const handleTemplateSelect = (templateId: string) => {
        const template = availableTemplates.find(t => t.id === templateId);
        if (template) {
            setSelectedTemplateId(templateId);
            setEmailSubject(template.subject);
            setEmailTemplate(template.body);
        }
    };

    const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
        const file = event.target.files?.[0];
        if (!file) return;

        const formData = new FormData();
        formData.append('file', file);

        try {
            await api.post(`/api/campaigns/${campaignId}/upload-contacts`, formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            });
            
            // Refresh campaign and contacts
            fetchCampaign();
            fetchContacts();
        } catch (err) {
            setError('Failed to upload contacts');
        }
    };

    const handleGenerateEmails = async () => {
        try {
            // Save template first
            await api.put(`/api/campaigns/${campaignId}`, {
                email_template: emailTemplate,
                email_subject: emailSubject
            });
            
            // Generate emails
            await api.post(`/api/campaigns/${campaignId}/generate-emails`);
            
            // Refresh campaign
            fetchCampaign();
        } catch (err) {
            setError('Failed to generate emails');
        }
    };

    const handleBulkExclude = async (exclude: boolean) => {
        try {
            await api.put(`/api/campaigns/${campaignId}/contacts/bulk-update`, {
                contact_ids: Array.from(selectedContacts),
                excluded: exclude
            });
            
            // Refresh contacts
            fetchContacts();
            setSelectedContacts(new Set());
        } catch (err) {
            setError('Failed to update contacts');
        }
    };

    const handleUpdateContact = async (contactId: string, data: any) => {
        try {
            await api.put(`/api/campaigns/${campaignId}/contacts/${contactId}`, data);
            
            // Update local state
            setContacts(contacts.map(c => 
                c.id === contactId ? { ...c, ...data } : c
            ));
        } catch (err) {
            setError('Failed to update contact');
        }
    };

    const toggleContactSelection = (contactId: string) => {
        const newSelection = new Set(selectedContacts);
        if (newSelection.has(contactId)) {
            newSelection.delete(contactId);
        } else {
            newSelection.add(contactId);
        }
        setSelectedContacts(newSelection);
    };

    const toggleAllContacts = () => {
        if (selectedContacts.size === filteredContacts.length) {
            setSelectedContacts(new Set());
        } else {
            setSelectedContacts(new Set(filteredContacts.map(c => c.id)));
        }
    };

    const filteredContacts = contacts.filter(contact => {
        const searchLower = searchTerm.toLowerCase();
        return (
            contact.first_name?.toLowerCase().includes(searchLower) ||
            contact.last_name?.toLowerCase().includes(searchLower) ||
            contact.email?.toLowerCase().includes(searchLower) ||
            contact.company?.toLowerCase().includes(searchLower) ||
            contact.title?.toLowerCase().includes(searchLower) ||
            contact.phone?.toLowerCase().includes(searchLower) ||
            contact.neighborhood?.toLowerCase().includes(searchLower)
        );
    });

    // Analytics data
    const enrichmentData = campaign ? [
        { name: 'Enriched', value: campaign.enriched_contacts, color: 'var(--green-9)' },
        { name: 'Failed', value: campaign.failed_enrichments, color: 'var(--red-9)' },
        { name: 'Pending', value: campaign.total_contacts - campaign.enriched_contacts - campaign.failed_enrichments, color: 'var(--gray-9)' }
    ] : [];

    if (isLoading) return <MainLayout onNewChat={() => {}}><Text>Loading...</Text></MainLayout>;
    if (!campaign) return <MainLayout onNewChat={() => {}}><Text>Campaign not found</Text></MainLayout>;

    return (
        <MainLayout onNewChat={() => {}}>
            <Box style={{ height: '100vh', backgroundColor: 'var(--gray-1)', overflow: 'auto' }}>
                {/* Header */}
                <Box style={{ padding: '1.5rem 2rem', borderBottom: '1px solid var(--gray-4)', backgroundColor: 'white' }}>
                    <Flex align="center" gap="3" mb="3">
                        <IconButton variant="ghost" onClick={() => navigate('/campaigns')}>
                            <ArrowLeftIcon />
                        </IconButton>
                        <Heading size="7" style={{ color: 'var(--gray-12)' }}>{campaign.name}</Heading>
                        <Badge color={getStatusColor(campaign.status)} size="2">
                            {getStatusLabel(campaign.status)}
                        </Badge>
                    </Flex>
                    
                    <Flex gap="4" style={{ color: 'var(--gray-10)' }}>
                        <Flex align="center" gap="2">
                            <PersonIcon />
                            <Text size="2">{campaign.owner_name}</Text>
                        </Flex>
                        <Text size="2">•</Text>
                        <Text size="2">Event: {new Date(campaign.event_date).toLocaleDateString()}</Text>
                        <Text size="2">•</Text>
                        <Text size="2">{campaign.event_type === 'virtual' ? 'Virtual' : 'In-Person'}</Text>
                    </Flex>
                </Box>

                {/* Error Message */}
                {error && (
                    <Box style={{ padding: '1rem 2rem' }}>
                        <Callout.Root color="red">
                            <Callout.Icon>
                                <InfoCircledIcon />
                            </Callout.Icon>
                            <Callout.Text>{error}</Callout.Text>
                        </Callout.Root>
                    </Box>
                )}

                {/* Tabs */}
                <Tabs.Root value={activeTab} onValueChange={setActiveTab}>
                    <Box style={{ padding: '0 2rem', backgroundColor: 'white', borderBottom: '1px solid var(--gray-4)' }}>
                        <Tabs.List>
                            <Tabs.Trigger value="overview">Overview</Tabs.Trigger>
                            <Tabs.Trigger value="contacts">Contacts ({campaign.total_contacts})</Tabs.Trigger>
                            <Tabs.Trigger value="emails">Email Template</Tabs.Trigger>
                            <Tabs.Trigger value="analytics">Analytics</Tabs.Trigger>
                            <Tabs.Trigger value="map">Map View</Tabs.Trigger>
                        </Tabs.List>
                    </Box>

                    <Box style={{ padding: '2rem' }}>
                        {/* Overview Tab */}
                        <Tabs.Content value="overview">
                            <Box style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem' }}>
                                {/* Campaign Details */}
                                <Card>
                                    <Heading size="4" mb="4">Campaign Details</Heading>
                                    <Flex direction="column" gap="3">
                                        <Box>
                                            <Text size="2" color="gray">Launch Date:</Text>
                                            <Text size="3" weight="medium">
                                                {new Date(campaign.launch_date).toLocaleDateString()}
                                            </Text>
                                        </Box>
                                        <Box>
                                            <Text size="2" color="gray">Event Date:</Text>
                                            <Text size="3" weight="medium">
                                                {new Date(campaign.event_date).toLocaleDateString()}
                                            </Text>
                                        </Box>
                                        {campaign.event_times && campaign.event_times.length > 0 && (
                                            <Box>
                                                <Text size="2" color="gray">Event Times:</Text>
                                                <Text size="3" weight="medium">
                                                    {campaign.event_times.join(', ')}
                                                </Text>
                                            </Box>
                                        )}
                                        {campaign.target_cities && (
                                            <Box>
                                                <Text size="2" color="gray">Target Cities:</Text>
                                                <Text size="3" weight="medium" style={{ whiteSpace: 'pre-wrap' }}>
                                                    {campaign.target_cities}
                                                </Text>
                                            </Box>
                                        )}
                                        {campaign.event_type === 'in_person' ? (
                                            <>
                                                <Box>
                                                    <Text size="2" color="gray">Hotel:</Text>
                                                    <Text size="3" weight="medium">{campaign.hotel_name}</Text>
                                                    <Text size="3">{campaign.hotel_address}</Text>
                                                </Box>
                                            </>
                                        ) : (
                                            <Box>
                                                <Text size="2" color="gray">Calendly Link:</Text>
                                                <Text size="3" weight="medium">{campaign.calendly_link}</Text>
                                            </Box>
                                        )}
                                    </Flex>
                                </Card>

                                {/* Quick Actions */}
                                <Card>
                                    <Heading size="4" mb="4">Quick Actions</Heading>
                                    <Flex direction="column" gap="3">
                                        {campaign.status === 'draft' && (
                                            <>
                                                <input
                                                    ref={fileInputRef}
                                                    type="file"
                                                    accept=".csv"
                                                    onChange={handleFileUpload}
                                                    style={{ display: 'none' }}
                                                />
                                                <Button onClick={() => fileInputRef.current?.click()}>
                                                    <UploadIcon />
                                                    Upload Contacts CSV
                                                </Button>
                                            </>
                                        )}
                                        
                                        {campaign.status === 'enriching' && enrichmentStatus && (
                                            <Box>
                                                <Flex align="center" justify="between" mb="2">
                                                    <Text size="2" weight="medium">Enrichment Progress</Text>
                                                    <Text size="2" color="blue">{enrichmentStatus.progress_percentage}%</Text>
                                                </Flex>
                                                <Box style={{ 
                                                    width: '100%', 
                                                    height: '8px', 
                                                    backgroundColor: 'var(--gray-4)', 
                                                    borderRadius: '4px',
                                                    overflow: 'hidden',
                                                    marginBottom: '1rem'
                                                }}>
                                                    <Box style={{
                                                        width: `${enrichmentStatus.progress_percentage}%`,
                                                        height: '100%',
                                                        backgroundColor: 'var(--blue-9)',
                                                        transition: 'width 0.3s ease'
                                                    }} />
                                                </Box>
                                                <Text size="1" color="gray">
                                                    {enrichmentStatus.enrichment_breakdown.success} enriched, 
                                                    {enrichmentStatus.enrichment_breakdown.failed} failed, 
                                                    {enrichmentStatus.enrichment_breakdown.processing} processing, 
                                                    {enrichmentStatus.enrichment_breakdown.pending} pending
                                                </Text>
                                            </Box>
                                        )}
                                        
                                        {campaign.status === 'ready_for_personalization' && (
                                            <Button onClick={handleGenerateEmails}>
                                                <EnvelopeClosedIcon />
                                                Generate Personalized Emails
                                            </Button>
                                        )}
                                        
                                        {campaign.status === 'ready_to_send' && (
                                            <Button disabled>
                                                <EnvelopeClosedIcon />
                                                Send Emails (Coming Soon)
                                            </Button>
                                        )}
                                        
                                        <Button variant="soft" onClick={fetchCampaign}>
                                            <ReloadIcon />
                                            Refresh Status
                                        </Button>
                                    </Flex>
                                </Card>

                                {/* Progress Overview */}
                                <Card style={{ gridColumn: 'span 2' }}>
                                    <Heading size="4" mb="4">Progress Overview</Heading>
                                    <Box style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '2rem' }}>
                                        <Box>
                                            <Text size="2" color="gray">Total Contacts:</Text>
                                            <Text size="6" weight="bold">{campaign.total_contacts}</Text>
                                        </Box>
                                        <Box>
                                            <Text size="2" color="gray">Enriched:</Text>
                                            <Text size="6" weight="bold" style={{ color: 'var(--green-9)' }}>
                                                {campaign.enriched_contacts}
                                            </Text>
                                        </Box>
                                        <Box>
                                            <Text size="2" color="gray">Emails Generated:</Text>
                                            <Text size="6" weight="bold" style={{ color: 'var(--blue-9)' }}>
                                                {campaign.emails_generated}
                                            </Text>
                                        </Box>
                                        <Box>
                                            <Text size="2" color="gray">Emails Sent:</Text>
                                            <Text size="6" weight="bold">{campaign.emails_sent}</Text>
                                        </Box>
                                    </Box>
                                </Card>
                            </Box>
                        </Tabs.Content>

                        {/* Contacts Tab */}
                        <Tabs.Content value="contacts">
                            <Card>
                                <Flex align="center" justify="between" mb="4">
                                    <Heading size="4">Contact List</Heading>
                                    <Flex gap="3" align="center">
                                        <TextField.Root
                                            placeholder="Search contacts..."
                                            value={searchTerm}
                                            onChange={(e) => setSearchTerm(e.target.value)}
                                            style={{ width: '300px' }}
                                        >
                                            <TextField.Slot>
                                                <MagnifyingGlassIcon />
                                            </TextField.Slot>
                                        </TextField.Root>
                                        
                                        {selectedContacts.size > 0 && (
                                            <DropdownMenu.Root>
                                                <DropdownMenu.Trigger>
                                                    <Button variant="soft">
                                                        Actions ({selectedContacts.size})
                                                        <DotsHorizontalIcon />
                                                    </Button>
                                                </DropdownMenu.Trigger>
                                                <DropdownMenu.Content>
                                                    <DropdownMenu.Item onClick={() => handleBulkExclude(true)}>
                                                        Exclude from Campaign
                                                    </DropdownMenu.Item>
                                                    <DropdownMenu.Item onClick={() => handleBulkExclude(false)}>
                                                        Include in Campaign
                                                    </DropdownMenu.Item>
                                                </DropdownMenu.Content>
                                            </DropdownMenu.Root>
                                        )}
                                    </Flex>
                                </Flex>

                                <Box style={{ overflowX: 'auto' }}>
                                    <Table.Root style={{ minWidth: '1200px' }}>
                                        <Table.Header>
                                            <Table.Row>
                                                <Table.ColumnHeaderCell style={{ position: 'sticky', left: 0, backgroundColor: 'var(--color-background)', zIndex: 1 }}>
                                                    <Checkbox
                                                        checked={selectedContacts.size === filteredContacts.length && filteredContacts.length > 0}
                                                        onCheckedChange={toggleAllContacts}
                                                    />
                                                </Table.ColumnHeaderCell>
                                                <Table.ColumnHeaderCell>First Name</Table.ColumnHeaderCell>
                                                <Table.ColumnHeaderCell>Last Name</Table.ColumnHeaderCell>
                                                <Table.ColumnHeaderCell>Email</Table.ColumnHeaderCell>
                                                <Table.ColumnHeaderCell>Phone</Table.ColumnHeaderCell>
                                                <Table.ColumnHeaderCell>Company</Table.ColumnHeaderCell>
                                                <Table.ColumnHeaderCell>Title</Table.ColumnHeaderCell>
                                                <Table.ColumnHeaderCell>Neighborhood</Table.ColumnHeaderCell>
                                                <Table.ColumnHeaderCell>Enrichment Status</Table.ColumnHeaderCell>
                                                <Table.ColumnHeaderCell>Email Status</Table.ColumnHeaderCell>
                                                <Table.ColumnHeaderCell>Actions</Table.ColumnHeaderCell>
                                            </Table.Row>
                                        </Table.Header>
                                        <Table.Body>
                                            {filteredContacts.map(contact => (
                                                <Table.Row key={contact.id}>
                                                    <Table.Cell style={{ position: 'sticky', left: 0, backgroundColor: 'var(--color-background)', zIndex: 1 }}>
                                                        <Checkbox
                                                            checked={selectedContacts.has(contact.id)}
                                                            onCheckedChange={() => toggleContactSelection(contact.id)}
                                                        />
                                                    </Table.Cell>
                                                    <Table.Cell>
                                                        {contact.first_name || '-'}
                                                    </Table.Cell>
                                                    <Table.Cell>
                                                        {contact.last_name || '-'}
                                                    </Table.Cell>
                                                    <Table.Cell>{contact.email || '-'}</Table.Cell>
                                                    <Table.Cell>{contact.enriched_phone || contact.phone || '-'}</Table.Cell>
                                                    <Table.Cell>{contact.enriched_company || contact.company || '-'}</Table.Cell>
                                                    <Table.Cell>{contact.enriched_title || contact.title || '-'}</Table.Cell>
                                                    <Table.Cell>{contact.neighborhood || '-'}</Table.Cell>
                                                    <Table.Cell>
                                                        <Badge 
                                                            color={
                                                                contact.enrichment_status === 'success' ? 'green' :
                                                                contact.enrichment_status === 'failed' ? 'red' :
                                                                contact.enrichment_status === 'processing' ? 'blue' : 'gray'
                                                            }
                                                        >
                                                            {contact.enrichment_status}
                                                        </Badge>
                                                        {contact.enrichment_status === 'success' && (
                                                            <Flex gap="1" mt="1">
                                                                {contact.email && <Badge size="1" color="blue">Email</Badge>}
                                                                {contact.enriched_phone && <Badge size="1" color="green">Phone</Badge>}
                                                                {contact.enriched_linkedin && <Badge size="1" color="cyan">LinkedIn</Badge>}
                                                            </Flex>
                                                        )}
                                                    </Table.Cell>
                                                    <Table.Cell>
                                                        <Badge 
                                                            color={
                                                                contact.email_status === 'generated' ? 'green' :
                                                                contact.email_status === 'sent' ? 'blue' : 'gray'
                                                            }
                                                        >
                                                            {contact.email_status}
                                                        </Badge>
                                                    </Table.Cell>
                                                    <Table.Cell>
                                                        <Flex gap="2">
                                                            {contact.personalized_email && (
                                                                <IconButton 
                                                                    size="1" 
                                                                    variant="ghost"
                                                                    onClick={() => {
                                                                        setPreviewContact(contact);
                                                                        setShowEmailPreview(true);
                                                                    }}
                                                                >
                                                                    <EnvelopeClosedIcon />
                                                                </IconButton>
                                                            )}
                                                            <IconButton 
                                                                size="1" 
                                                                variant="ghost"
                                                                color={contact.excluded ? 'green' : 'red'}
                                                                onClick={() => handleUpdateContact(contact.id, { excluded: !contact.excluded })}
                                                            >
                                                                {contact.excluded ? <CheckIcon /> : <Cross2Icon />}
                                                            </IconButton>
                                                        </Flex>
                                                    </Table.Cell>
                                                </Table.Row>
                                            ))}
                                        </Table.Body>
                                    </Table.Root>
                                </Box>
                            </Card>
                        </Tabs.Content>

                        {/* Email Template Tab */}
                        <Tabs.Content value="emails">
                            <Card>
                                <Heading size="4" mb="4">Email Template</Heading>
                                
                                <Flex direction="column" gap="4">
                                    <Box>
                                        <Flex align="center" justify="between" mb="2">
                                            <Text as="label" size="2" weight="medium">
                                                Select Template
                                            </Text>
                                            <Button 
                                                size="1" 
                                                variant="ghost"
                                                onClick={() => navigate('/template-manager')}
                                            >
                                                Manage Templates
                                            </Button>
                                        </Flex>
                                        <Select.Root 
                                            value={selectedTemplateId} 
                                            onValueChange={handleTemplateSelect}
                                        >
                                            <Select.Trigger placeholder="Choose a template or start from scratch..." />
                                            <Select.Content>
                                                <Select.Item value="">Start from scratch</Select.Item>
                                                <Select.Separator />
                                                {availableTemplates.map(template => (
                                                    <Select.Item key={template.id} value={template.id}>
                                                        <Flex direction="column" gap="1">
                                                            <Text size="2" weight="medium">{template.name}</Text>
                                                            <Text size="1" color="gray">{template.goal}</Text>
                                                        </Flex>
                                                    </Select.Item>
                                                ))}
                                            </Select.Content>
                                        </Select.Root>
                                    </Box>
                                    
                                    <Box>
                                        <Text as="label" size="2" mb="1" weight="medium">
                                            Email Subject
                                        </Text>
                                        <TextField.Root
                                            value={emailSubject}
                                            onChange={(e) => setEmailSubject(e.target.value)}
                                            placeholder="Join us for an exclusive event..."
                                        />
                                    </Box>
                                    
                                    <Box>
                                        <Text as="label" size="2" mb="1" weight="medium">
                                            Email Template
                                        </Text>
                                        <TextArea
                                            value={emailTemplate}
                                            onChange={(e) => setEmailTemplate(e.target.value)}
                                            placeholder="Dear {first_name},\n\nWe're excited to invite you to our upcoming event..."
                                            rows={15}
                                        />
                                        <Text size="1" color="gray" mt="1">
                                            Available variables: {'{first_name}'}, {'{last_name}'}, {'{company}'}, {'{title}'}, {'{event_date}'}, {'{event_time}'}, {'{hotel_name}'}, {'{hotel_address}'}, {'{calendly_link}'}
                                        </Text>
                                    </Box>
                                    
                                    <Flex gap="3">
                                        <Button 
                                            onClick={() => api.put(`/api/campaigns/${campaignId}`, { 
                                                email_template: emailTemplate, 
                                                email_subject: emailSubject 
                                            })}
                                        >
                                            Save Template
                                        </Button>
                                        {campaign.status === 'ready_for_personalization' && (
                                            <Button onClick={handleGenerateEmails}>
                                                Generate Emails
                                            </Button>
                                        )}
                                    </Flex>
                                </Flex>
                            </Card>
                        </Tabs.Content>

                        {/* Analytics Tab */}
                        <Tabs.Content value="analytics">
                            <Box style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem' }}>
                                {/* Enrichment Stats */}
                                <Card>
                                    <Heading size="4" mb="4">Enrichment Statistics</Heading>
                                    <Box style={{ height: '300px' }}>
                                        <ResponsiveContainer width="100%" height="100%">
                                            <PieChart>
                                                <Pie
                                                    data={enrichmentData}
                                                    cx="50%"
                                                    cy="50%"
                                                    outerRadius={80}
                                                    fill="#8884d8"
                                                    dataKey="value"
                                                    label
                                                >
                                                    {enrichmentData.map((entry, index) => (
                                                        <Cell key={`cell-${index}`} fill={entry.color} />
                                                    ))}
                                                </Pie>
                                                <Tooltip />
                                            </PieChart>
                                        </ResponsiveContainer>
                                    </Box>
                                </Card>

                                {/* Success Rates */}
                                <Card>
                                    <Heading size="4" mb="4">Success Rates</Heading>
                                    <Flex direction="column" gap="4">
                                        <Box>
                                            <Flex align="center" justify="between" mb="2">
                                                <Text size="2">Enrichment Success Rate</Text>
                                                <Text size="2" weight="bold">
                                                    {campaign.total_contacts > 0 
                                                        ? Math.round((campaign.enriched_contacts / campaign.total_contacts) * 100) 
                                                        : 0}%
                                                </Text>
                                            </Flex>
                                            <Box style={{ 
                                                width: '100%', 
                                                height: '8px', 
                                                backgroundColor: 'var(--gray-4)', 
                                                borderRadius: '4px',
                                                overflow: 'hidden'
                                            }}>
                                                <Box style={{
                                                    width: `${campaign.total_contacts > 0 
                                                        ? (campaign.enriched_contacts / campaign.total_contacts) * 100 
                                                        : 0}%`,
                                                    height: '100%',
                                                    backgroundColor: 'var(--green-9)'
                                                }} />
                                            </Box>
                                        </Box>
                                        
                                        <Box>
                                            <Flex align="center" justify="between" mb="2">
                                                <Text size="2">Email Generation Rate</Text>
                                                <Text size="2" weight="bold">
                                                    {campaign.enriched_contacts > 0 
                                                        ? Math.round((campaign.emails_generated / campaign.enriched_contacts) * 100) 
                                                        : 0}%
                                                </Text>
                                            </Flex>
                                            <Box style={{ 
                                                width: '100%', 
                                                height: '8px', 
                                                backgroundColor: 'var(--gray-4)', 
                                                borderRadius: '4px',
                                                overflow: 'hidden'
                                            }}>
                                                <Box style={{
                                                    width: `${campaign.enriched_contacts > 0 
                                                        ? (campaign.emails_generated / campaign.enriched_contacts) * 100 
                                                        : 0}%`,
                                                    height: '100%',
                                                    backgroundColor: 'var(--blue-9)'
                                                }} />
                                            </Box>
                                        </Box>
                                    </Flex>
                                </Card>

                                {/* Email and Phone Capture Rates */}
                                <Card style={{ gridColumn: 'span 2' }}>
                                    <Heading size="4" mb="4">Data Capture Rates</Heading>
                                    <Box style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '2rem' }}>
                                        <Box>
                                            <Flex align="center" justify="between" mb="2">
                                                <Text size="2" weight="medium">Email Capture Rate</Text>
                                                <Text size="3" weight="bold" color="blue">
                                                    {(() => {
                                                        const contactsWithEmail = contacts.filter(c => c.email).length;
                                                        return campaign.total_contacts > 0 
                                                            ? Math.round((contactsWithEmail / campaign.total_contacts) * 100) 
                                                            : 0;
                                                    })()}%
                                                </Text>
                                            </Flex>
                                            <Box style={{ 
                                                width: '100%', 
                                                height: '12px', 
                                                backgroundColor: 'var(--gray-4)', 
                                                borderRadius: '6px',
                                                overflow: 'hidden'
                                            }}>
                                                <Box style={{
                                                    width: `${(() => {
                                                        const contactsWithEmail = contacts.filter(c => c.email).length;
                                                        return campaign.total_contacts > 0 
                                                            ? (contactsWithEmail / campaign.total_contacts) * 100 
                                                            : 0;
                                                    })()}%`,
                                                    height: '100%',
                                                    backgroundColor: 'var(--blue-9)'
                                                }} />
                                            </Box>
                                            <Text size="1" color="gray" mt="2">
                                                {contacts.filter(c => c.email).length} of {campaign.total_contacts} contacts have emails
                                            </Text>
                                        </Box>

                                        <Box>
                                            <Flex align="center" justify="between" mb="2">
                                                <Text size="2" weight="medium">Phone Capture Rate</Text>
                                                <Text size="3" weight="bold" color="green">
                                                    {(() => {
                                                        const contactsWithPhone = contacts.filter(c => c.enriched_phone || c.phone).length;
                                                        return campaign.total_contacts > 0 
                                                            ? Math.round((contactsWithPhone / campaign.total_contacts) * 100) 
                                                            : 0;
                                                    })()}%
                                                </Text>
                                            </Flex>
                                            <Box style={{ 
                                                width: '100%', 
                                                height: '12px', 
                                                backgroundColor: 'var(--gray-4)', 
                                                borderRadius: '6px',
                                                overflow: 'hidden'
                                            }}>
                                                <Box style={{
                                                    width: `${(() => {
                                                        const contactsWithPhone = contacts.filter(c => c.enriched_phone || c.phone).length;
                                                        return campaign.total_contacts > 0 
                                                            ? (contactsWithPhone / campaign.total_contacts) * 100 
                                                            : 0;
                                                    })()}%`,
                                                    height: '100%',
                                                    backgroundColor: 'var(--green-9)'
                                                }} />
                                            </Box>
                                            <Text size="1" color="gray" mt="2">
                                                {contacts.filter(c => c.enriched_phone || c.phone).length} of {campaign.total_contacts} contacts have phones
                                            </Text>
                                        </Box>
                                    </Box>

                                    {/* Breakdown by source */}
                                    <Box mt="4" style={{ borderTop: '1px solid var(--gray-4)', paddingTop: '1rem' }}>
                                        <Text size="2" weight="medium" mb="3">Data Sources</Text>
                                        <Box style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1rem' }}>
                                            <Box>
                                                <Text size="1" color="gray">Original Emails</Text>
                                                <Text size="3" weight="bold">
                                                    {contacts.filter(c => c.email && !c.enriched_phone).length}
                                                </Text>
                                            </Box>
                                            <Box>
                                                <Text size="1" color="gray">Enriched Emails</Text>
                                                <Text size="3" weight="bold" color="blue">
                                                    {contacts.filter(c => c.email && c.enrichment_status === 'success').length}
                                                </Text>
                                            </Box>
                                            <Box>
                                                <Text size="1" color="gray">Original Phones</Text>
                                                <Text size="3" weight="bold">
                                                    {contacts.filter(c => c.phone && !c.enriched_phone).length}
                                                </Text>
                                            </Box>
                                            <Box>
                                                <Text size="1" color="gray">Enriched Phones</Text>
                                                <Text size="3" weight="bold" color="green">
                                                    {contacts.filter(c => c.enriched_phone).length}
                                                </Text>
                                            </Box>
                                        </Box>
                                    </Box>
                                </Card>
                            </Box>
                        </Tabs.Content>

                        {/* Map View Tab */}
                        <Tabs.Content value="map">
                            <Card>
                                <Heading size="4" mb="4">Contact Locations</Heading>
                                
                                {(() => {
                                    // Get all non-excluded contacts
                                    const allContacts = contacts.filter(c => !c.excluded);
                                    
                                    // Separate contacts with and without coordinates
                                    const contactsWithCoords = allContacts
                                        .map(c => ({
                                            ...c,
                                            coords: getNeighborhoodCoords(c.neighborhood)
                                        }))
                                        .filter(c => c.coords !== null);
                                    
                                    const contactsWithoutCoords = allContacts
                                        .filter(c => !getNeighborhoodCoords(c.neighborhood));
                                    
                                    // Count neighborhoods for mapped contacts
                                    const neighborhoodCounts = contactsWithCoords.reduce((acc, contact) => {
                                        const key = contact.neighborhood || 'Unknown';
                                        acc[key] = (acc[key] || 0) + 1;
                                        return acc;
                                    }, {} as Record<string, number>);
                                    
                                    // Count unmapped neighborhoods
                                    const unmappedNeighborhoods = contactsWithoutCoords.reduce((acc, contact) => {
                                        const key = contact.neighborhood || 'No neighborhood';
                                        acc[key] = (acc[key] || 0) + 1;
                                        return acc;
                                    }, {} as Record<string, number>);
                                    
                                    return (
                                        <Box>
                                            <Flex gap="4" mb="4">
                                                <Badge size="2" color="green">
                                                    Mapped: {contactsWithCoords.length} contacts
                                                </Badge>
                                                <Badge size="2" color="orange">
                                                    Unmapped: {contactsWithoutCoords.length} contacts
                                                </Badge>
                                                <Badge size="2" color="gray">
                                                    Total: {allContacts.length} contacts
                                                </Badge>
                                            </Flex>
                                            
                                            {contactsWithCoords.length === 0 ? (
                                                <Box p="4">
                                                    <Text color="gray">No contacts with valid neighborhood data to display on map.</Text>
                                                </Box>
                                            ) : (
                                                <Box style={{ height: '600px', position: 'relative' }}>
                                                    <MapContainer
                                                        center={[33.5186, -86.8104]} // Alabama center (Birmingham)
                                                        zoom={7}
                                                        style={{ height: '100%', width: '100%' }}
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
                                                                    radius={Math.min(30, 10 + count * 2)}
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
                                                    
                                                    <Box 
                                                        style={{ 
                                                            position: 'absolute', 
                                                            top: '1rem', 
                                                            right: '1rem', 
                                                            backgroundColor: 'white', 
                                                            padding: '1rem',
                                                            borderRadius: '8px',
                                                            boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
                                                            zIndex: 1000,
                                                            maxHeight: '400px',
                                                            overflowY: 'auto',
                                                            maxWidth: '300px'
                                                        }}
                                                    >
                                                        <Text size="2" weight="bold" mb="2">Mapped Neighborhoods</Text>
                                                        {Object.entries(neighborhoodCounts)
                                                            .sort(([, a], [, b]) => b - a)
                                                            .map(([neighborhood, count]) => (
                                                                <Flex key={neighborhood} justify="between" gap="3" mb="1">
                                                                    <Text size="1">{neighborhood}</Text>
                                                                    <Text size="1" weight="medium">{count}</Text>
                                                                </Flex>
                                                            ))
                                                        }
                                                        
                                                        {contactsWithoutCoords.length > 0 && (
                                                            <>
                                                                <Text size="2" weight="bold" mt="3" mb="2" color="orange">
                                                                    Unmapped Neighborhoods
                                                                </Text>
                                                                <Text size="1" color="gray" mb="2">
                                                                    (Add coordinates to display on map)
                                                                </Text>
                                                                {Object.entries(unmappedNeighborhoods)
                                                                    .sort(([, a], [, b]) => b - a)
                                                                    .slice(0, 20) // Show top 20
                                                                    .map(([neighborhood, count]) => (
                                                                        <Flex key={neighborhood} justify="between" gap="3" mb="1">
                                                                            <Text size="1" color="orange">{neighborhood}</Text>
                                                                            <Text size="1" weight="medium" color="orange">{count}</Text>
                                                                        </Flex>
                                                                    ))
                                                                }
                                                                {Object.keys(unmappedNeighborhoods).length > 20 && (
                                                                    <Text size="1" color="gray" mt="2">
                                                                        ... and {Object.keys(unmappedNeighborhoods).length - 20} more
                                                                    </Text>
                                                                )}
                                                            </>
                                                        )}
                                                    </Box>
                                                </Box>
                                            )}
                                        </Box>
                                    );
                                })()}
                            </Card>
                        </Tabs.Content>
                    </Box>
                </Tabs.Root>

                {/* Email Preview Dialog */}
                <Dialog.Root open={showEmailPreview} onOpenChange={setShowEmailPreview}>
                    <Dialog.Content style={{ maxWidth: 600 }}>
                        <Dialog.Title>Email Preview</Dialog.Title>
                        {previewContact && (
                            <Box mt="4">
                                <Box mb="3">
                                    <Text size="2" color="gray">To:</Text>
                                    <Text size="3">{previewContact.email}</Text>
                                </Box>
                                <Box mb="3">
                                    <Text size="2" color="gray">Subject:</Text>
                                    <Text size="3" weight="medium">
                                        {previewContact.personalized_subject || campaign.email_subject}
                                    </Text>
                                </Box>
                                <Box>
                                    <Text size="2" color="gray">Body:</Text>
                                    <Box 
                                        style={{ 
                                            backgroundColor: 'var(--gray-2)', 
                                            padding: '1rem', 
                                            borderRadius: '8px',
                                            marginTop: '0.5rem',
                                            whiteSpace: 'pre-wrap'
                                        }}
                                    >
                                        <Text size="2">{previewContact.personalized_email}</Text>
                                    </Box>
                                </Box>
                                {editingContact === previewContact.id ? (
                                    <Box mt="4">
                                        <TextArea
                                            value={editingEmail}
                                            onChange={(e) => setEditingEmail(e.target.value)}
                                            rows={10}
                                        />
                                        <Flex gap="2" mt="3">
                                            <Button 
                                                size="2"
                                                onClick={() => {
                                                    handleUpdateContact(previewContact.id, { 
                                                        personalized_email: editingEmail 
                                                    });
                                                    setEditingContact(null);
                                                }}
                                            >
                                                Save
                                            </Button>
                                            <Button 
                                                size="2" 
                                                variant="soft"
                                                onClick={() => setEditingContact(null)}
                                            >
                                                Cancel
                                            </Button>
                                        </Flex>
                                    </Box>
                                ) : (
                                    <Flex gap="3" mt="4" justify="end">
                                        <Button 
                                            variant="soft"
                                            onClick={() => {
                                                setEditingEmail(previewContact.personalized_email || '');
                                                setEditingContact(previewContact.id);
                                            }}
                                        >
                                            <Pencil1Icon />
                                            Edit
                                        </Button>
                                        <Dialog.Close>
                                            <Button variant="soft">Close</Button>
                                        </Dialog.Close>
                                    </Flex>
                                )}
                            </Box>
                        )}
                    </Dialog.Content>
                </Dialog.Root>
            </Box>
        </MainLayout>
    );
};

export default CampaignDetailPage; 