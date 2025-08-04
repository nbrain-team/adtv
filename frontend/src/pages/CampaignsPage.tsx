import { useState, useEffect } from 'react';
import { Box, Flex, Heading, Text, Card, Button, Badge, Dialog, TextField, Select, TextArea, Callout, IconButton, AlertDialog } from '@radix-ui/themes';
import { PlusIcon, CalendarIcon, PersonIcon, EnvelopeClosedIcon, BarChartIcon, InfoCircledIcon, TrashIcon } from '@radix-ui/react-icons';
import { MainLayout } from '../components/MainLayout';
import { useNavigate } from 'react-router-dom';
import api from '../api';
import { CampaignDataHub } from '../components/CampaignDataHub';

interface Campaign {
    id: string;
    name: string;
    owner_name: string;
    owner_email: string;
    owner_phone?: string;
    launch_date: string;
    event_type: 'virtual' | 'in_person';
    event_date: string;
    event_times?: string[];
    target_cities?: string;
    hotel_name?: string;
    hotel_address?: string;
    calendly_link?: string;
    status: string;
    total_contacts: number;
    enriched_contacts: number;
    failed_enrichments: number;
    emails_generated: number;
    emails_sent: number;
    created_at: string;
    updated_at: string;
}

const CAMPAIGN_OWNERS = [
    { value: 'kalena_conley', label: 'Kalena Conley', email: 'kalena@adtvmedia.com', phone: '619-374-7405' },
    { value: 'evan_jones', label: 'Evan Jones', email: 'evan@adtvmedia.com', phone: '619-374-2561' },
    { value: 'sigrid_smith', label: 'Sigrid Smith', email: 'sigrid@adtvmedia.com', phone: '619-292-8580' },
    { value: 'amy_dodsworth', label: 'Amy Dodsworth', email: 'amy@adtvmedia.com', phone: '619-259-0014' },
    { value: 'bailey_jacobs', label: 'Bailey Jacobs', email: 'bailey@adtvmedia.com', phone: '619-333-0342' }
];

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

const CampaignsPage = () => {
    const [campaigns, setCampaigns] = useState<Campaign[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [showCreateDialog, setShowCreateDialog] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [deletingCampaignId, setDeletingCampaignId] = useState<string | null>(null);
    const navigate = useNavigate();

    // Form state
    const [formData, setFormData] = useState({
        name: '',
        owner: '',
        launch_date: '',
        event_type: 'in_person' as 'virtual' | 'in_person',
        event_date: '',
        event_times: [''],
        target_cities: '',
        hotel_name: '',
        hotel_address: '',
        calendly_link: ''
    });

    useEffect(() => {
        fetchCampaigns();
    }, []);

    const fetchCampaigns = async () => {
        try {
            const response = await api.get('/api/campaigns');
            setCampaigns(response.data);
        } catch (err) {
            setError('Failed to load campaigns');
        } finally {
            setIsLoading(false);
        }
    };

    const handleCreateCampaign = async () => {
        try {
            const selectedOwner = CAMPAIGN_OWNERS.find(o => o.value === formData.owner);
            if (!selectedOwner) return;

            const campaignData = {
                name: formData.name,
                owner_name: selectedOwner.label,
                owner_email: selectedOwner.email,
                // owner_phone: selectedOwner.phone,  // TEMPORARILY DISABLED UNTIL MIGRATION RUNS
                launch_date: new Date(formData.launch_date).toISOString(),
                event_type: formData.event_type,
                event_date: new Date(formData.event_date).toISOString(),
                event_times: formData.event_times.filter(time => time.trim() !== ''),
                target_cities: formData.target_cities,
                hotel_name: formData.event_type === 'in_person' ? formData.hotel_name : undefined,
                hotel_address: formData.event_type === 'in_person' ? formData.hotel_address : undefined,
                calendly_link: formData.event_type === 'virtual' ? formData.calendly_link : undefined
            };

            console.log('Creating campaign with data:', campaignData);
            const response = await api.post('/api/campaigns', campaignData);
            console.log('Campaign created response:', response.data);
            
            // Refresh the campaigns list to ensure we have the latest data
            await fetchCampaigns();
            
            setShowCreateDialog(false);
            
            // Reset form
            setFormData({
                name: '',
                owner: '',
                launch_date: '',
                event_type: 'in_person',
                event_date: '',
                event_times: [''],
                target_cities: '',
                hotel_name: '',
                hotel_address: '',
                calendly_link: ''
            });
            
            // Navigate to the new campaign
            if (response.data && response.data.id) {
                navigate(`/campaigns/${response.data.id}`);
            }
        } catch (err) {
            console.error('Create campaign error:', err);
            setError('Failed to create campaign');
        }
    };

    const handleDeleteCampaign = async (campaignId: string) => {
        try {
            await api.delete(`/api/campaigns/${campaignId}`);
            setCampaigns(campaigns.filter(c => c.id !== campaignId));
            setDeletingCampaignId(null);
        } catch (err) {
            console.error('Delete campaign error:', err);
            setError('Failed to delete campaign');
            setDeletingCampaignId(null);
        }
    };

    const getProgressPercentage = (campaign: Campaign) => {
        if (campaign.total_contacts === 0) return 0;
        return Math.round((campaign.enriched_contacts / campaign.total_contacts) * 100);
    };

    return (
        <MainLayout onNewChat={() => {}}>
            <Box style={{ height: '100vh', backgroundColor: 'var(--gray-1)', overflow: 'auto' }}>
                <Box style={{ padding: '1.5rem 2rem', borderBottom: '1px solid var(--gray-4)', backgroundColor: 'white' }}>
                    <Flex align="center" justify="between">
                        <Box>
                            <Heading size="7" style={{ color: 'var(--gray-12)' }}>Event Campaign Builder</Heading>
                            <Text as="p" size="3" style={{ color: 'var(--gray-10)', marginTop: '0.25rem' }}>
                                Create and manage your event marketing campaigns
                            </Text>
                        </Box>
                        <Button onClick={() => setShowCreateDialog(true)}>
                            <PlusIcon />
                            New Campaign
                        </Button>
                    </Flex>
                </Box>

                <Box style={{ padding: '2rem' }}>
                    {error && (
                        <Callout.Root color="red" mb="4">
                            <Callout.Icon>
                                <InfoCircledIcon />
                            </Callout.Icon>
                            <Callout.Text>{error}</Callout.Text>
                        </Callout.Root>
                    )}

                    {isLoading ? (
                        <Text>Loading campaigns...</Text>
                    ) : campaigns.length === 0 ? (
                        <Card style={{ textAlign: 'center', padding: '3rem' }}>
                            <Text size="4" color="gray">No campaigns yet</Text>
                            <Text size="2" color="gray" mt="2">Create your first campaign to get started</Text>
                        </Card>
                    ) : (
                        <Box style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(350px, 1fr))', gap: '1.5rem' }}>
                            {campaigns.map(campaign => (
                                <Card 
                                    key={campaign.id} 
                                    style={{ cursor: 'pointer', transition: 'all 0.2s', position: 'relative' }}
                                    onClick={(e) => {
                                        // Don't navigate if clicking on delete button
                                        if ((e.target as HTMLElement).closest('[data-delete-button]')) {
                                            return;
                                        }
                                        console.log('Navigating to campaign:', campaign.id);
                                        // Temporary fix: use window.location for navigation
                                        window.location.href = `/campaigns/${campaign.id}`;
                                        // navigate(`/campaigns/${campaign.id}`);
                                    }}
                                >
                                    <IconButton
                                        data-delete-button
                                        size="2"
                                        color="red"
                                        variant="ghost"
                                        style={{
                                            position: 'absolute',
                                            bottom: '1rem',
                                            left: '1rem',
                                            zIndex: 10
                                        }}
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            setDeletingCampaignId(campaign.id);
                                        }}
                                    >
                                        <TrashIcon />
                                    </IconButton>
                                    
                                    <Flex direction="column" gap="3">
                                        <Flex align="center" justify="between">
                                            <Heading size="4">{campaign.name}</Heading>
                                            <Badge color={getStatusColor(campaign.status)}>
                                                {getStatusLabel(campaign.status)}
                                            </Badge>
                                        </Flex>

                                        <Flex direction="column" gap="2">
                                            <Flex align="center" gap="2">
                                                <PersonIcon />
                                                <Text size="2">{campaign.owner_name}</Text>
                                            </Flex>
                                            <Flex align="center" gap="2">
                                                <CalendarIcon />
                                                <Text size="2">
                                                    Event: {new Date(campaign.event_date).toLocaleDateString()}
                                                    {' • '}
                                                    {campaign.event_type === 'virtual' ? 'Virtual' : 'In-Person'}
                                                </Text>
                                            </Flex>
                                        </Flex>

                                        <Box>
                                            <Flex align="center" justify="between" mb="2">
                                                <Text size="2" color="gray">Progress</Text>
                                                <Text size="2" weight="medium">
                                                    {campaign.enriched_contacts}/{campaign.total_contacts} contacts
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
                                                    width: `${getProgressPercentage(campaign)}%`,
                                                    height: '100%',
                                                    backgroundColor: 'var(--blue-9)',
                                                    transition: 'width 0.3s ease'
                                                }} />
                                            </Box>
                                        </Box>

                                        <Flex gap="4" style={{ borderTop: '1px solid var(--gray-4)', paddingTop: '1rem' }}>
                                            <Flex direction="column" align="center" style={{ flex: 1 }}>
                                                <Text size="1" color="gray">Enriched</Text>
                                                <Text size="3" weight="bold">{campaign.enriched_contacts}</Text>
                                            </Flex>
                                            <Flex direction="column" align="center" style={{ flex: 1 }}>
                                                <Text size="1" color="gray">Emails</Text>
                                                <Text size="3" weight="bold">{campaign.emails_generated}</Text>
                                            </Flex>
                                            <Flex direction="column" align="center" style={{ flex: 1 }}>
                                                <Text size="1" color="gray">Sent</Text>
                                                <Text size="3" weight="bold">{campaign.emails_sent}</Text>
                                            </Flex>
                                        </Flex>
                                    </Flex>
                                </Card>
                            ))}
                        </Box>
                    )}
                    
                    {/* Campaign Data Hub */}
                    <CampaignDataHub />
                </Box>

                <Dialog.Root open={showCreateDialog} onOpenChange={setShowCreateDialog}>
                    <Dialog.Content style={{ maxWidth: 500 }}>
                        <Dialog.Title>Create New Campaign</Dialog.Title>
                        
                        <Flex direction="column" gap="4" mt="4">
                            <Box>
                                <Text as="label" size="2" mb="1" weight="medium">
                                    Campaign Name
                                </Text>
                                <TextField.Root
                                    value={formData.name}
                                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                                    placeholder="Q1 2024 Roadshow"
                                />
                            </Box>

                            <Box>
                                <Text as="label" size="2" mb="1" weight="medium">
                                    Campaign Owner
                                </Text>
                                <Select.Root value={formData.owner} onValueChange={(value) => setFormData({ ...formData, owner: value })}>
                                    <Select.Trigger placeholder="Select owner" />
                                    <Select.Content>
                                        {CAMPAIGN_OWNERS.map(owner => (
                                            <Select.Item key={owner.value} value={owner.value}>
                                                {owner.label}
                                            </Select.Item>
                                        ))}
                                    </Select.Content>
                                </Select.Root>
                            </Box>

                            <Box>
                                <Text as="label" size="2" mb="1" weight="medium">
                                    Target Cities
                                </Text>
                                <TextArea
                                    value={formData.target_cities}
                                    onChange={(e) => setFormData({ ...formData, target_cities: e.target.value })}
                                    placeholder="Enter target cities, one per line"
                                    rows={3}
                                />
                            </Box>

                            <Flex gap="3">
                                <Box style={{ flex: 1 }}>
                                    <Text as="label" size="2" mb="1" weight="medium">
                                        Launch Date
                                    </Text>
                                    <TextField.Root
                                        type="date"
                                        value={formData.launch_date}
                                        onChange={(e) => setFormData({ ...formData, launch_date: e.target.value })}
                                    />
                                </Box>
                                <Box style={{ flex: 1 }}>
                                    <Text as="label" size="2" mb="1" weight="medium">
                                        Event Date
                                    </Text>
                                    <TextField.Root
                                        type="date"
                                        value={formData.event_date}
                                        onChange={(e) => setFormData({ ...formData, event_date: e.target.value })}
                                    />
                                </Box>
                            </Flex>

                            <Box>
                                <Flex align="center" justify="between" mb="2">
                                    <Text as="label" size="2" weight="medium">
                                        Event Times
                                    </Text>
                                    <Button 
                                        size="1" 
                                        variant="soft"
                                        onClick={() => setFormData({ ...formData, event_times: [...formData.event_times, ''] })}
                                    >
                                        <PlusIcon />
                                        Add Time
                                    </Button>
                                </Flex>
                                <Flex direction="column" gap="2">
                                    {formData.event_times.map((time, index) => (
                                        <Flex key={index} gap="2" align="center">
                                            <TextField.Root
                                                type="time"
                                                value={time}
                                                onChange={(e) => {
                                                    const newTimes = [...formData.event_times];
                                                    newTimes[index] = e.target.value;
                                                    setFormData({ ...formData, event_times: newTimes });
                                                }}
                                                style={{ flex: 1 }}
                                            />
                                            {formData.event_times.length > 1 && (
                                                <Button
                                                    size="1"
                                                    variant="soft"
                                                    color="red"
                                                    onClick={() => {
                                                        const newTimes = formData.event_times.filter((_, i) => i !== index);
                                                        setFormData({ ...formData, event_times: newTimes });
                                                    }}
                                                >
                                                    Remove
                                                </Button>
                                            )}
                                        </Flex>
                                    ))}
                                </Flex>
                            </Box>

                            <Box>
                                <Text as="label" size="2" mb="1" weight="medium">
                                    Event Type
                                </Text>
                                <Select.Root 
                                    value={formData.event_type} 
                                    onValueChange={(value: 'virtual' | 'in_person') => setFormData({ ...formData, event_type: value })}
                                >
                                    <Select.Trigger />
                                    <Select.Content>
                                        <Select.Item value="in_person">In-Person</Select.Item>
                                        <Select.Item value="virtual">Virtual</Select.Item>
                                    </Select.Content>
                                </Select.Root>
                            </Box>

                            {formData.event_type === 'in_person' ? (
                                <>
                                    <Box>
                                        <Text as="label" size="2" mb="1" weight="medium">
                                            Hotel Name
                                        </Text>
                                        <TextField.Root
                                            value={formData.hotel_name}
                                            onChange={(e) => setFormData({ ...formData, hotel_name: e.target.value })}
                                            placeholder="Marriott Downtown"
                                        />
                                    </Box>
                                    <Box>
                                        <Text as="label" size="2" mb="1" weight="medium">
                                            Hotel Address
                                        </Text>
                                        <TextArea
                                            value={formData.hotel_address}
                                            onChange={(e) => setFormData({ ...formData, hotel_address: e.target.value })}
                                            placeholder="123 Main St, City, State ZIP"
                                            rows={2}
                                        />
                                    </Box>
                                </>
                            ) : (
                                <Box>
                                    <Text as="label" size="2" mb="1" weight="medium">
                                        Calendly Link
                                    </Text>
                                    <TextField.Root
                                        value={formData.calendly_link}
                                        onChange={(e) => setFormData({ ...formData, calendly_link: e.target.value })}
                                        placeholder="https://calendly.com/yourname/meeting"
                                    />
                                </Box>
                            )}
                        </Flex>

                        <Flex gap="3" mt="5" justify="end">
                            <Dialog.Close>
                                <Button variant="soft" color="gray">
                                    Cancel
                                </Button>
                            </Dialog.Close>
                            <Button 
                                onClick={handleCreateCampaign}
                                disabled={!formData.name || !formData.owner || !formData.launch_date || !formData.event_date}
                            >
                                Create Campaign
                            </Button>
                        </Flex>
                    </Dialog.Content>
                </Dialog.Root>

                <AlertDialog.Root open={!!deletingCampaignId} onOpenChange={(open) => !open && setDeletingCampaignId(null)}>
                    <AlertDialog.Content style={{ maxWidth: 450 }}>
                        <AlertDialog.Title>Delete Campaign</AlertDialog.Title>
                        <AlertDialog.Description size="2">
                            Are you sure you want to delete this campaign? This action cannot be undone.
                            All contacts and data associated with this campaign will be permanently deleted.
                        </AlertDialog.Description>

                        <Flex gap="3" mt="4" justify="end">
                            <AlertDialog.Cancel>
                                <Button variant="soft" color="gray">
                                    Cancel
                                </Button>
                            </AlertDialog.Cancel>
                            <AlertDialog.Action>
                                <Button 
                                    variant="solid" 
                                    color="red"
                                    onClick={() => deletingCampaignId && handleDeleteCampaign(deletingCampaignId)}
                                >
                                    Delete Campaign
                                </Button>
                            </AlertDialog.Action>
                        </Flex>
                    </AlertDialog.Content>
                </AlertDialog.Root>
            </Box>
        </MainLayout>
    );
};

export default CampaignsPage; 