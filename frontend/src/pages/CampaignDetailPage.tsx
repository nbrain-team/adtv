import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
    Box, Flex, Heading, Text, Card, Button, Badge, Tabs, Table, 
    Checkbox, TextField, TextArea, Callout, IconButton, Dialog,
    DropdownMenu, ScrollArea
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
    enrichment_status: string;
    email_status: string;
    excluded: boolean;
    personalized_email?: string;
    personalized_subject?: string;
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

    useEffect(() => {
        if (campaignId) {
            fetchCampaign();
            fetchContacts();
        }
    }, [campaignId]);

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
            contact.company?.toLowerCase().includes(searchLower)
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

                                <ScrollArea style={{ height: '600px' }}>
                                    <Table.Root>
                                        <Table.Header>
                                            <Table.Row>
                                                <Table.ColumnHeaderCell>
                                                    <Checkbox
                                                        checked={selectedContacts.size === filteredContacts.length && filteredContacts.length > 0}
                                                        onCheckedChange={toggleAllContacts}
                                                    />
                                                </Table.ColumnHeaderCell>
                                                <Table.ColumnHeaderCell>Name</Table.ColumnHeaderCell>
                                                <Table.ColumnHeaderCell>Email</Table.ColumnHeaderCell>
                                                <Table.ColumnHeaderCell>Company</Table.ColumnHeaderCell>
                                                <Table.ColumnHeaderCell>Enrichment</Table.ColumnHeaderCell>
                                                <Table.ColumnHeaderCell>Email Status</Table.ColumnHeaderCell>
                                                <Table.ColumnHeaderCell>Actions</Table.ColumnHeaderCell>
                                            </Table.Row>
                                        </Table.Header>
                                        <Table.Body>
                                            {filteredContacts.map(contact => (
                                                <Table.Row key={contact.id}>
                                                    <Table.Cell>
                                                        <Checkbox
                                                            checked={selectedContacts.has(contact.id)}
                                                            onCheckedChange={() => toggleContactSelection(contact.id)}
                                                        />
                                                    </Table.Cell>
                                                    <Table.Cell>
                                                        {contact.first_name} {contact.last_name}
                                                    </Table.Cell>
                                                    <Table.Cell>{contact.email}</Table.Cell>
                                                    <Table.Cell>{contact.company}</Table.Cell>
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
                                </ScrollArea>
                            </Card>
                        </Tabs.Content>

                        {/* Email Template Tab */}
                        <Tabs.Content value="emails">
                            <Card>
                                <Heading size="4" mb="4">Email Template</Heading>
                                
                                <Flex direction="column" gap="4">
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
                                            Available variables: {'{first_name}'}, {'{last_name}'}, {'{company}'}, {'{title}'}
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
                            </Box>
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