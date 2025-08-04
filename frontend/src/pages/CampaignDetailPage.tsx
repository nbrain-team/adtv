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
import { MapContainer, TileLayer, CircleMarker, Popup, Marker } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import React from 'react'; // Added for React.Fragment

// Fix for default markers in react-leaflet
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
    iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
    iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
    shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png'
});

// Create custom hotel icon
const hotelIcon = new L.Icon({
    iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png',
    shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
    shadowSize: [41, 41]
});

// Add spinning animation CSS
const spinAnimation = `
    @keyframes spin {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
    }
`;

interface Campaign {
    id: string;
    name: string;
    owner_name: string;
    owner_email: string;
    owner_phone?: string;
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
    content?: string; // Some templates use content instead of body
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
    // Additional Alabama neighborhoods
    'Research Park': [34.7243, -86.6389],
    'Research Park, Huntsville': [34.7243, -86.6389],
    'Weatherly Heights': [34.7304, -86.5861],
    'Weatherly Heights, Huntsville': [34.7304, -86.5861],
    'Meridianville': [34.8515, -86.5722],
    'New Market': [34.9062, -86.4269],
    'Ryland': [34.8098, -86.4633],
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
    
    // Extract just the city name from formats like "Madison, Alabama, USA"
    const cityName = neighborhood.split(',')[0].trim();
    
    // Try exact match with full string first
    if (NEIGHBORHOOD_COORDS[neighborhood]) {
        return NEIGHBORHOOD_COORDS[neighborhood];
    }
    
    // Try match with just city name
    if (NEIGHBORHOOD_COORDS[cityName]) {
        return NEIGHBORHOOD_COORDS[cityName];
    }
    
    // Try case-insensitive match with full string
    const lowerNeighborhood = neighborhood.toLowerCase();
    for (const [key, coords] of Object.entries(NEIGHBORHOOD_COORDS)) {
        if (key.toLowerCase() === lowerNeighborhood) {
            return coords;
        }
    }
    
    // Try case-insensitive match with just city name
    const lowerCityName = cityName.toLowerCase();
    for (const [key, coords] of Object.entries(NEIGHBORHOOD_COORDS)) {
        if (key.toLowerCase() === lowerCityName) {
            return coords;
        }
    }
    
    return null;
};

// Function to geocode address (using Nominatim - free OpenStreetMap geocoding)
const geocodeAddress = async (address: string): Promise<[number, number] | null> => {
    if (!address) return null;
    
    try {
        const response = await fetch(
            `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(address)}&limit=1`
        );
        const data = await response.json();
        
        if (data && data.length > 0) {
            return [parseFloat(data[0].lat), parseFloat(data[0].lon)];
        }
    } catch (error) {
        console.error('Error geocoding address:', error);
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
    const [selectedTemplateId, setSelectedTemplateId] = useState<string>('scratch');
    const [isLoadingTemplates, setIsLoadingTemplates] = useState(false);
    const [isEditingCampaign, setIsEditingCampaign] = useState(false);
    const [editedCampaign, setEditedCampaign] = useState<Campaign | null>(null);
    const [isEditingContact, setIsEditingContact] = useState(false);
    const [editingContactData, setEditingContactData] = useState<any>(null);
    const [hotelCoords, setHotelCoords] = useState<[number, number] | null>(null);
    const [expandedContactId, setExpandedContactId] = useState<string | null>(null);
    const [showBulkEditModal, setShowBulkEditModal] = useState(false);
    const [bulkEditField, setBulkEditField] = useState<string>('');
    const [bulkEditValue, setBulkEditValue] = useState<string>('');

    useEffect(() => {
        if (campaignId) {
            fetchCampaign();
            fetchContacts();
            fetchTemplates();
        }
    }, [campaignId]);

    useEffect(() => {
        if (campaign?.status === 'enriching') {
            const interval = setInterval(() => {
                fetchEnrichmentStatus();
                fetchCampaign(); // Also refresh campaign data
            }, 5000); // Check every 5 seconds
            fetchEnrichmentStatus(); // Initial fetch
            return () => clearInterval(interval);
        } else if (campaign?.status === 'ready_for_personalization' && !enrichmentStatus) {
            // One-time fetch when returning to a completed enrichment
            fetchEnrichmentStatus();
        }
    }, [campaign?.status]);

    useEffect(() => {
        if (campaign?.status === 'generating_emails') {
            const interval = setInterval(() => {
                fetchCampaign(); // Refresh campaign data to check if emails are done
                fetchContacts(); // Refresh contacts to see generated emails
            }, 3000); // Check every 3 seconds
            return () => clearInterval(interval);
        }
    }, [campaign?.status]);

    useEffect(() => {
        if (campaign) {
            setEmailTemplate(campaign.email_template || '');
            setEmailSubject(campaign.email_subject || '');
            setEditedCampaign(campaign);
            
            // Auto-navigate to emails tab when generating emails
            if (campaign.status === 'generating_emails' && activeTab !== 'emails') {
                setActiveTab('emails');
            }
        }
    }, [campaign]);

    // Poll for status updates when generating emails
    useEffect(() => {
        if (campaign?.status === 'generating_emails') {
            const interval = setInterval(() => {
                fetchCampaign();
                fetchContacts();
            }, 3000);
            
            return () => clearInterval(interval);
        }
    }, [campaign?.status, campaignId]);

    // Geocode hotel address when campaign loads
    useEffect(() => {
        const geocodeHotel = async () => {
            if (campaign?.event_type === 'in_person' && campaign?.hotel_address) {
                const coords = await geocodeAddress(campaign.hotel_address);
                setHotelCoords(coords);
            }
        };
        
        geocodeHotel();
    }, [campaign?.hotel_address, campaign?.event_type]);

    const fetchCampaign = async () => {
        try {
            console.log('Fetching campaign with ID:', campaignId);
            const response = await api.get(`/api/campaigns/${campaignId}`);
            console.log('Campaign data received:', response.data);
            setCampaign(response.data);
        } catch (err) {
            console.error('Failed to load campaign:', err);
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
            
            // If enrichment is complete, refresh the campaign and contacts
            if (response.data.progress_percentage === 100 && campaign?.status === 'enriching') {
                // Force a complete refresh after a short delay
                setTimeout(() => {
                    fetchCampaign();
                    fetchContacts();
                }, 2000); // 2 second delay to ensure backend has updated
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
        if (templateId === 'scratch') {
            // Clear template for starting from scratch
            setSelectedTemplateId('scratch');
            setEmailTemplate('');
            setEmailSubject('');
            return;
        }
        
        const template = availableTemplates.find(t => t.id === templateId);
        if (template) {
            setSelectedTemplateId(templateId);
            
            // Replace template variables with campaign data
            let processedBody = template.body || template.content || '';
            let processedSubject = template.subject || `Invitation to ${campaign?.name}`;
            
            // Replace common variables
            const replacements: Record<string, string> = {
                '{{State}}': 'your state',
                '{{City}}': campaign?.target_cities?.split('\n')[0] || 'your city',
                '{{MM}}': campaign?.owner_name || '',
                '[[YourName]]': campaign?.owner_name || '',
                '[[DestinationCity]]': campaign?.target_cities?.split('\n')[0] || '',
                '[[DaysUntilEvent]]': (() => {
                    if (campaign?.event_date) {
                        const days = Math.ceil((new Date(campaign.event_date).getTime() - new Date().getTime()) / (1000 * 60 * 60 * 24));
                        return days > 0 ? days.toString() : 'upcoming';
                    }
                    return 'upcoming';
                })(),
                '[[ExampleCities]]': campaign?.target_cities?.replace(/\n/g, ', ') || ''
            };
            
            // Apply replacements
            Object.entries(replacements).forEach(([key, value]) => {
                processedBody = processedBody.replace(new RegExp(key.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'g'), value);
                processedSubject = processedSubject.replace(new RegExp(key.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'g'), value);
            });
            
            setEmailTemplate(processedBody);
            setEmailSubject(processedSubject);
        }
    };

    const handleSaveCampaign = async () => {
        if (!editedCampaign) return;
        
        try {
            const updateData = {
                name: editedCampaign.name,
                launch_date: editedCampaign.launch_date,
                event_date: editedCampaign.event_date,
                event_times: editedCampaign.event_times,
                target_cities: editedCampaign.target_cities,
                hotel_name: editedCampaign.hotel_name,
                hotel_address: editedCampaign.hotel_address,
                calendly_link: editedCampaign.calendly_link
            };
            
            await api.put(`/api/campaigns/${campaignId}`, updateData);
            setCampaign(editedCampaign);
            setIsEditingCampaign(false);
        } catch (err) {
            setError('Failed to update campaign');
        }
    };

    const handleCancelEdit = () => {
        setEditedCampaign(campaign);
        setIsEditingCampaign(false);
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

    const handleBulkEdit = async () => {
        if (!bulkEditField || !bulkEditValue) return;
        
        try {
            const updateData: any = {};
            updateData[bulkEditField] = bulkEditValue;
            
            // Update all selected contacts
            const promises = Array.from(selectedContacts).map(contactId => 
                api.put(`/api/campaigns/${campaignId}/contacts/${contactId}`, updateData)
            );
            
            await Promise.all(promises);
            
            // Update local state
            setContacts(contacts.map(c => 
                selectedContacts.has(c.id) ? { ...c, ...updateData } : c
            ));
            
            setShowBulkEditModal(false);
            setBulkEditField('');
            setBulkEditValue('');
            setSelectedContacts(new Set());
        } catch (err) {
            setError('Failed to update contacts');
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

    if (isLoading) {
        return (
            <MainLayout onNewChat={() => {}}>
                <Box style={{ height: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    <Flex direction="column" align="center" gap="3">
                        <div style={{ animation: 'spin 1s linear infinite' }}>
                            <ReloadIcon width="32" height="32" />
                        </div>
                        <Text size="3">Loading campaign...</Text>
                    </Flex>
                </Box>
            </MainLayout>
        );
    }
    
    if (error) {
        return (
            <MainLayout onNewChat={() => {}}>
                <Box style={{ height: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    <Flex direction="column" align="center" gap="3">
                        <Text size="4" color="red">Error: {error}</Text>
                        <Button onClick={() => navigate('/campaigns')}>
                            <ArrowLeftIcon />
                            Back to Campaigns
                        </Button>
                    </Flex>
                </Box>
            </MainLayout>
        );
    }
    
    if (!campaign) {
        return (
            <MainLayout onNewChat={() => {}}>
                <Box style={{ height: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    <Flex direction="column" align="center" gap="3">
                        <Text size="4">Campaign not found</Text>
                        <Button onClick={() => navigate('/campaigns')}>
                            <ArrowLeftIcon />
                            Back to Campaigns
                        </Button>
                    </Flex>
                </Box>
            </MainLayout>
        );
    }

    return (
        <MainLayout onNewChat={() => {}}>
            <style dangerouslySetInnerHTML={{ __html: spinAnimation }} />
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
                    
                    <Flex gap="4" style={{ color: 'var(--gray-12)' }}>
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

                {/* Progress Steps Bar */}
                <Box style={{ padding: '1rem 2rem', backgroundColor: 'white', borderBottom: '1px solid var(--gray-4)' }}>
                    {(() => {
                        const steps = [
                            { 
                                id: 1,
                                name: 'Create Campaign', 
                                status: 'completed',
                                action: null
                            },
                            { 
                                id: 2,
                                name: 'Upload & Enrich', 
                                status: campaign.total_contacts > 0 ? 
                                    (campaign.status === 'enriching' ? 'active' : 'completed') : 'pending',
                                action: campaign.total_contacts === 0 ? () => setActiveTab('overview') : null
                            },
                            { 
                                id: 3,
                                name: 'Create Emails', 
                                status: campaign.status === 'generating_emails' ? 'active' :
                                       campaign.emails_generated > 0 ? 'completed' : 
                                       campaign.status === 'ready_for_personalization' ? 'ready' : 'pending',
                                action: campaign.status === 'ready_for_personalization' ? () => setActiveTab('emails') : null
                            },
                            { 
                                id: 4,
                                name: 'Review & Approve', 
                                status: campaign.emails_generated > 0 ? 
                                    (campaign.status === 'ready_to_send' ? 'ready' : 'pending') : 'pending',
                                action: campaign.emails_generated > 0 ? () => setActiveTab('contacts') : null
                            },
                            {
                                id: 5,
                                name: 'Send Emails',
                                status: campaign.status === 'sending' ? 'active' :
                                       campaign.emails_sent > 0 ? 'completed' : 
                                       campaign.status === 'ready_to_send' ? 'ready' : 'pending',
                                action: campaign.status === 'ready_to_send' ? () => setActiveTab('contacts') : null
                            }
                        ];

                        const currentStep = steps.findIndex(s => s.status === 'active' || s.status === 'ready') + 1 || steps.length;
                        const completedSteps = steps.filter(s => s.status === 'completed').length;

                        return (
                            <Box>
                                <Flex align="center" gap="3" style={{ position: 'relative' }}>
                                    {/* Progress line background */}
                                    <Box style={{
                                        position: 'absolute',
                                        top: '20px',
                                        left: '40px',
                                        right: '40px',
                                        height: '4px',
                                        backgroundColor: 'var(--gray-3)',
                                        zIndex: 0
                                    }}>
                                        {/* Progress line fill */}
                                        <Box style={{
                                            height: '100%',
                                            width: `${(completedSteps / (steps.length - 1)) * 100}%`,
                                            backgroundColor: 'var(--green-9)',
                                            transition: 'width 0.3s ease'
                                        }} />
                                    </Box>

                                    {steps.map((step, index) => (
                                        <Box key={step.id} style={{ flex: 1, position: 'relative', zIndex: 1 }}>
                                            <Flex direction="column" align="center" gap="1">
                                                <Button
                                                    size="3"
                                                    variant={step.status === 'completed' ? 'solid' : 
                                                            step.status === 'active' || step.status === 'ready' ? 'soft' : 'ghost'}
                                                    color={step.status === 'completed' ? 'green' :
                                                          step.status === 'active' ? 'blue' :
                                                          step.status === 'ready' ? 'blue' : 'gray'}
                                                    style={{
                                                        width: '40px',
                                                        height: '40px',
                                                        borderRadius: '50%',
                                                        padding: 0,
                                                        cursor: step.action ? 'pointer' : 'default',
                                                        boxShadow: step.status === 'active' ? '0 0 0 4px var(--blue-3)' : 'none',
                                                        backgroundColor: step.status === 'completed' || step.status === 'active' || step.status === 'ready' 
                                                            ? undefined 
                                                            : 'var(--color-background)',
                                                        border: step.status === 'ghost' ? '2px solid var(--gray-6)' : undefined,
                                                        position: 'relative',
                                                        zIndex: 2
                                                    }}
                                                    onClick={step.action || undefined}
                                                    disabled={!step.action}
                                                >
                                                    {step.status === 'completed' ? '✓' : step.id}
                                                </Button>
                                                <Text size="1" weight="medium" align="center">
                                                    {step.name}
                                                </Text>
                                                {step.status === 'ready' && (
                                                    <Badge size="1" color="blue">Ready</Badge>
                                                )}
                                            </Flex>
                                        </Box>
                                    ))}
                                </Flex>

                                {/* Next Step Call to Action */}
                                {(() => {
                                    const nextStep = steps.find(s => s.status === 'ready' || (s.status === 'pending' && s.action));
                                    if (nextStep) {
                                        return (
                                            <Box mt="3" style={{ textAlign: 'center' }}>
                                                <Button 
                                                    size="2" 
                                                    onClick={nextStep.action || undefined}
                                                    disabled={!nextStep.action}
                                                >
                                                    Continue to {nextStep.name}
                                                </Button>
                                            </Box>
                                        );
                                    }
                                    return null;
                                })()}
                            </Box>
                        );
                    })()}
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
                            <Tabs.Trigger value="emails">Generate Emails</Tabs.Trigger>
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
                                    <Flex align="center" justify="between" mb="4">
                                        <Heading size="4">Campaign Details</Heading>
                                        {!isEditingCampaign ? (
                                            <Button 
                                                variant="ghost" 
                                                size="2"
                                                onClick={() => setIsEditingCampaign(true)}
                                            >
                                                <Pencil1Icon />
                                                Edit
                                            </Button>
                                        ) : (
                                            <Flex gap="2">
                                                <Button 
                                                    size="2"
                                                    onClick={handleSaveCampaign}
                                                >
                                                    <CheckIcon />
                                                    Save
                                                </Button>
                                                <Button 
                                                    size="2" 
                                                    variant="soft"
                                                    onClick={handleCancelEdit}
                                                >
                                                    <Cross2Icon />
                                                    Cancel
                                                </Button>
                                            </Flex>
                                        )}
                                    </Flex>
                                    
                                    <Flex direction="column" gap="3">
                                        {/* Campaign Name */}
                                        <Box>
                                            <Text size="2" weight="bold" style={{ color: 'var(--gray-12)' }}>Campaign Name: </Text>
                                            {!isEditingCampaign ? (
                                                <Text size="2" style={{ color: 'var(--gray-12)' }}>
                                                    {campaign.name}
                                                </Text>
                                            ) : (
                                                <TextField.Root
                                                    value={editedCampaign?.name || ''}
                                                    onChange={(e) => setEditedCampaign({
                                                        ...editedCampaign!,
                                                        name: e.target.value
                                                    })}
                                                    style={{ marginTop: '0.25rem' }}
                                                />
                                            )}
                                        </Box>
                                        
                                        {/* Launch Date */}
                                        <Box>
                                            <Text size="2" weight="bold" style={{ color: 'var(--gray-12)' }}>Launch Date: </Text>
                                            {!isEditingCampaign ? (
                                                <Text size="2" style={{ color: 'var(--gray-12)' }}>
                                                    {new Date(campaign.launch_date).toLocaleDateString()}
                                                </Text>
                                            ) : (
                                                <input
                                                    type="date"
                                                    value={editedCampaign?.launch_date ? 
                                                        new Date(editedCampaign.launch_date).toISOString().split('T')[0] : ''
                                                    }
                                                    onChange={(e) => setEditedCampaign({
                                                        ...editedCampaign!,
                                                        launch_date: new Date(e.target.value).toISOString()
                                                    })}
                                                    style={{ 
                                                        marginTop: '0.25rem',
                                                        padding: '0.5rem',
                                                        borderRadius: '4px',
                                                        border: '1px solid var(--gray-6)',
                                                        width: '100%'
                                                    }}
                                                />
                                            )}
                                        </Box>
                                        
                                        {/* Event Date */}
                                        <Box>
                                            <Text size="2" weight="bold" style={{ color: 'var(--gray-12)' }}>Event Date: </Text>
                                            {!isEditingCampaign ? (
                                                <Text size="2" style={{ color: 'var(--gray-12)' }}>
                                                    {new Date(campaign.event_date).toLocaleDateString()}
                                                </Text>
                                            ) : (
                                                <input
                                                    type="date"
                                                    value={editedCampaign?.event_date ? 
                                                        new Date(editedCampaign.event_date).toISOString().split('T')[0] : ''
                                                    }
                                                    onChange={(e) => setEditedCampaign({
                                                        ...editedCampaign!,
                                                        event_date: new Date(e.target.value).toISOString()
                                                    })}
                                                    style={{ 
                                                        marginTop: '0.25rem',
                                                        padding: '0.5rem',
                                                        borderRadius: '4px',
                                                        border: '1px solid var(--gray-6)',
                                                        width: '100%'
                                                    }}
                                                />
                                            )}
                                        </Box>
                                        
                                        {/* Event Times */}
                                        {(campaign.event_times && campaign.event_times.length > 0) || isEditingCampaign ? (
                                            <Box>
                                                <Text size="2" weight="bold" style={{ color: 'var(--gray-12)' }}>Event Times: </Text>
                                                {!isEditingCampaign ? (
                                                    <Text size="2" style={{ color: 'var(--gray-12)' }}>
                                                        {campaign.event_times?.join(', ')}
                                                    </Text>
                                                ) : (
                                                    <TextField.Root
                                                        value={editedCampaign?.event_times?.join(', ') || ''}
                                                        onChange={(e) => setEditedCampaign({
                                                            ...editedCampaign!,
                                                            event_times: e.target.value.split(',').map(t => t.trim()).filter(t => t)
                                                        })}
                                                        placeholder="e.g., 10:00 AM, 2:00 PM"
                                                        style={{ marginTop: '0.25rem' }}
                                                    />
                                                )}
                                            </Box>
                                        ) : null}
                                        
                                        {/* Target Cities */}
                                        {campaign.target_cities || isEditingCampaign ? (
                                            <Box>
                                                <Text size="2" weight="bold" style={{ color: 'var(--gray-12)' }}>Target Cities: </Text>
                                                {!isEditingCampaign ? (
                                                    <Text size="2" style={{ color: 'var(--gray-12)', whiteSpace: 'pre-wrap' }}>
                                                        {campaign.target_cities}
                                                    </Text>
                                                ) : (
                                                    <TextArea
                                                        value={editedCampaign?.target_cities || ''}
                                                        onChange={(e) => setEditedCampaign({
                                                            ...editedCampaign!,
                                                            target_cities: e.target.value
                                                        })}
                                                        placeholder="Enter cities, one per line"
                                                        rows={3}
                                                        style={{ marginTop: '0.25rem' }}
                                                    />
                                                )}
                                            </Box>
                                        ) : null}
                                        
                                        {/* Event Type Specific Fields */}
                                        {campaign.event_type === 'in_person' ? (
                                            <>
                                                <Box>
                                                    <Text size="2" weight="bold" style={{ color: 'var(--gray-12)' }}>Hotel Name: </Text>
                                                    {!isEditingCampaign ? (
                                                        <Text size="2" style={{ color: 'var(--gray-12)' }}>
                                                            {campaign.hotel_name || '-'}
                                                        </Text>
                                                    ) : (
                                                        <TextField.Root
                                                            value={editedCampaign?.hotel_name || ''}
                                                            onChange={(e) => setEditedCampaign({
                                                                ...editedCampaign!,
                                                                hotel_name: e.target.value
                                                            })}
                                                            style={{ marginTop: '0.25rem' }}
                                                        />
                                                    )}
                                                </Box>
                                                <Box>
                                                    <Text size="2" weight="bold" style={{ color: 'var(--gray-12)' }}>Hotel Address: </Text>
                                                    {!isEditingCampaign ? (
                                                        <Text size="2" style={{ color: 'var(--gray-12)' }}>
                                                            {campaign.hotel_address || '-'}
                                                        </Text>
                                                    ) : (
                                                        <TextField.Root
                                                            value={editedCampaign?.hotel_address || ''}
                                                            onChange={(e) => setEditedCampaign({
                                                                ...editedCampaign!,
                                                                hotel_address: e.target.value
                                                            })}
                                                            style={{ marginTop: '0.25rem' }}
                                                        />
                                                    )}
                                                </Box>
                                            </>
                                        ) : (
                                            <Box>
                                                <Text size="2" weight="bold" style={{ color: 'var(--gray-12)' }}>Calendly Link: </Text>
                                                {!isEditingCampaign ? (
                                                    <Text size="2" style={{ color: 'var(--gray-12)' }}>
                                                        {campaign.calendly_link || '-'}
                                                    </Text>
                                                ) : (
                                                    <TextField.Root
                                                        value={editedCampaign?.calendly_link || ''}
                                                        onChange={(e) => setEditedCampaign({
                                                            ...editedCampaign!,
                                                            calendly_link: e.target.value
                                                        })}
                                                        style={{ marginTop: '0.25rem' }}
                                                    />
                                                )}
                                            </Box>
                                        )}
                                    </Flex>
                                </Card>

                                {/* Quick Actions */}
                                <Card>
                                    <Flex align="center" justify="between" mb="4">
                                        <Heading size="4">Quick Actions</Heading>
                                        <Button 
                                            variant="ghost" 
                                            size="2"
                                            onClick={() => {
                                                fetchCampaign();
                                                fetchContacts();
                                                if (campaign?.status === 'enriching') {
                                                    fetchEnrichmentStatus();
                                                }
                                            }}
                                        >
                                            <ReloadIcon />
                                            Refresh
                                        </Button>
                                    </Flex>
                                    <Flex direction="column" gap="3">
                                        {/* Debug log the campaign status */}
                                        {console.log('Campaign status for upload button:', campaign.status)}
                                        {(campaign.status === 'draft' || campaign.total_contacts === 0) && (
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
                                    </Flex>
                                </Card>

                                {/* Map View */}
                                <Card style={{ gridColumn: 'span 2' }}>
                                    <Heading size="4" mb="4">Contact Locations</Heading>
                                    
                                    {campaign.total_contacts === 0 ? (
                                        <Box style={{ 
                                            height: '400px', 
                                            display: 'flex', 
                                            alignItems: 'center', 
                                            justifyContent: 'center',
                                            backgroundColor: 'var(--gray-2)',
                                            borderRadius: '8px'
                                        }}>
                                            <Text size="3" color="gray">Awaiting Map View...</Text>
                                        </Box>
                                    ) : (
                                        <Box>
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
                                                
                                                return (
                                                    <Box>
                                                        <Flex gap="2" mb="3">
                                                            <Badge size="1" color="green">
                                                                {contactsWithCoords.length} mapped
                                                            </Badge>
                                                            <Badge size="1" color="orange">
                                                                {contactsWithoutCoords.length} unmapped
                                                            </Badge>
                                                        </Flex>
                                                        
                                                        {contactsWithCoords.length === 0 ? (
                                                            <Box style={{ 
                                                                height: '350px', 
                                                                display: 'flex', 
                                                                alignItems: 'center', 
                                                                justifyContent: 'center',
                                                                backgroundColor: 'var(--gray-2)',
                                                                borderRadius: '8px'
                                                            }}>
                                                                <Text size="2" color="gray">No contacts with valid location data</Text>
                                                            </Box>
                                                        ) : (
                                                            <Box style={{ height: '350px', position: 'relative' }}>
                                                                <MapContainer
                                                                    center={[33.5186, -86.8104]} // Alabama center (Birmingham)
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
                                                                                radius={Math.min(20, 8 + count * 2)}
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
                                                                    
                                                                    {/* Hotel Marker */}
                                                                    {hotelCoords && campaign.event_type === 'in_person' && (
                                                                        <Marker 
                                                                            position={hotelCoords} 
                                                                            icon={hotelIcon}
                                                                        >
                                                                            <Popup>
                                                                                <Box>
                                                                                    <Text weight="bold">{campaign.hotel_name || 'Event Hotel'}</Text>
                                                                                    <br />
                                                                                    <Text size="1">{campaign.hotel_address}</Text>
                                                                                </Box>
                                                                            </Popup>
                                                                        </Marker>
                                                                    )}
                                                                </MapContainer>
                                                            </Box>
                                                        )}
                                                    </Box>
                                                );
                                            })()}
                                        </Box>
                                    )}
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
                                                    <DropdownMenu.Separator />
                                                    <DropdownMenu.Item onClick={() => setShowBulkEditModal(true)}>
                                                        <Pencil1Icon style={{ marginRight: '8px' }} />
                                                        Bulk Edit
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
                                                <React.Fragment key={contact.id}>
                                                    <Table.Row 
                                                        style={{ cursor: 'pointer' }}
                                                        onClick={(e) => {
                                                            // Don't expand if clicking on checkbox or action buttons
                                                            if ((e.target as HTMLElement).closest('button, input[type="checkbox"]')) return;
                                                            setExpandedContactId(expandedContactId === contact.id ? null : contact.id);
                                                        }}
                                                    >
                                                        <Table.Cell style={{ position: 'sticky', left: 0, backgroundColor: 'var(--color-background)', zIndex: 1 }}>
                                                            <Checkbox
                                                                checked={selectedContacts.has(contact.id)}
                                                                onCheckedChange={() => toggleContactSelection(contact.id)}
                                                                onClick={(e) => e.stopPropagation()}
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
                                                                        onClick={(e) => {
                                                                            e.stopPropagation();
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
                                                                    onClick={(e) => {
                                                                        e.stopPropagation();
                                                                        handleUpdateContact(contact.id, { excluded: !contact.excluded });
                                                                    }}
                                                                >
                                                                    {contact.excluded ? <CheckIcon /> : <Cross2Icon />}
                                                                </IconButton>
                                                            </Flex>
                                                        </Table.Cell>
                                                    </Table.Row>
                                                    
                                                    {/* Expanded Row */}
                                                    {expandedContactId === contact.id && (
                                                        <Table.Row>
                                                            <Table.Cell colSpan={11} style={{ backgroundColor: 'var(--gray-2)', padding: '1rem' }}>
                                                                <Box>
                                                                    <Flex justify="between" align="center" mb="3">
                                                                        <Heading size="3">Contact Details</Heading>
                                                                        <Button 
                                                                            size="2" 
                                                                            variant="soft"
                                                                            onClick={() => {
                                                                                setEditingContactData(contact);
                                                                                setIsEditingContact(true);
                                                                            }}
                                                                        >
                                                                            <Pencil1Icon />
                                                                            Edit Contact
                                                                        </Button>
                                                                    </Flex>
                                                                    
                                                                    <Box style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem' }}>
                                                                        {/* Basic Info */}
                                                                        <Box>
                                                                            <Text size="2" weight="bold" color="gray">Basic Information</Text>
                                                                            <Box mt="2">
                                                                                <Text size="1" color="gray">First Name</Text>
                                                                                <Text size="2">{contact.first_name || '-'}</Text>
                                                                            </Box>
                                                                            <Box mt="2">
                                                                                <Text size="1" color="gray">Last Name</Text>
                                                                                <Text size="2">{contact.last_name || '-'}</Text>
                                                                            </Box>
                                                                            <Box mt="2">
                                                                                <Text size="1" color="gray">Email</Text>
                                                                                <Text size="2">{contact.email || '-'}</Text>
                                                                            </Box>
                                                                            <Box mt="2">
                                                                                <Text size="1" color="gray">Phone</Text>
                                                                                <Text size="2">{contact.phone || '-'}</Text>
                                                                            </Box>
                                                                        </Box>
                                                                        
                                                                        {/* Original Data */}
                                                                        <Box>
                                                                            <Text size="2" weight="bold" color="gray">Original Data</Text>
                                                                            <Box mt="2">
                                                                                <Text size="1" color="gray">Company</Text>
                                                                                <Text size="2">{contact.company || '-'}</Text>
                                                                            </Box>
                                                                            <Box mt="2">
                                                                                <Text size="1" color="gray">Title</Text>
                                                                                <Text size="2">{contact.title || '-'}</Text>
                                                                            </Box>
                                                                            <Box mt="2">
                                                                                <Text size="1" color="gray">Neighborhood</Text>
                                                                                <Text size="2">{contact.neighborhood || '-'}</Text>
                                                                            </Box>
                                                                        </Box>
                                                                        
                                                                        {/* Enriched Data */}
                                                                        <Box>
                                                                            <Text size="2" weight="bold" color="gray">Enriched Data</Text>
                                                                            <Box mt="2">
                                                                                <Text size="1" color="gray">Enriched Company</Text>
                                                                                <Text size="2">{contact.enriched_company || '-'}</Text>
                                                                            </Box>
                                                                            <Box mt="2">
                                                                                <Text size="1" color="gray">Enriched Title</Text>
                                                                                <Text size="2">{contact.enriched_title || '-'}</Text>
                                                                            </Box>
                                                                            <Box mt="2">
                                                                                <Text size="1" color="gray">Enriched Phone</Text>
                                                                                <Text size="2">{contact.enriched_phone || '-'}</Text>
                                                                            </Box>
                                                                            <Box mt="2">
                                                                                <Text size="1" color="gray">LinkedIn</Text>
                                                                                <Text size="2">{contact.enriched_linkedin || '-'}</Text>
                                                                            </Box>
                                                                            <Box mt="2">
                                                                                <Text size="1" color="gray">Website</Text>
                                                                                <Text size="2">{contact.enriched_website || '-'}</Text>
                                                                            </Box>
                                                                            <Box mt="2">
                                                                                <Text size="1" color="gray">Industry</Text>
                                                                                <Text size="2">{contact.enriched_industry || '-'}</Text>
                                                                            </Box>
                                                                            <Box mt="2">
                                                                                <Text size="1" color="gray">Company Size</Text>
                                                                                <Text size="2">{contact.enriched_company_size || '-'}</Text>
                                                                            </Box>
                                                                            <Box mt="2">
                                                                                <Text size="1" color="gray">Location</Text>
                                                                                <Text size="2">{contact.enriched_location || '-'}</Text>
                                                                            </Box>
                                                                        </Box>
                                                                    </Box>
                                                                </Box>
                                                            </Table.Cell>
                                                        </Table.Row>
                                                    )}
                                                </React.Fragment>
                                            ))}
                                        </Table.Body>
                                    </Table.Root>
                                </Box>
                            </Card>
                        </Tabs.Content>

                        {/* Generate Emails Tab */}
                        <Tabs.Content value="emails">
                            <Card>
                                <Heading size="4" mb="4">Generate Personalized Emails</Heading>
                                
                                {campaign.status === 'ready_for_personalization' ? (
                                    <Flex direction="column" gap="4">
                                        <Callout.Root color="blue">
                                            <Callout.Icon>
                                                <InfoCircledIcon />
                                            </Callout.Icon>
                                            <Callout.Text>
                                                {campaign.enriched_contacts} contacts are ready for email personalization. 
                                                Configure your email template below and generate personalized emails.
                                            </Callout.Text>
                                        </Callout.Root>

                                        <Box>
                                            <Flex align="center" justify="between" mb="2">
                                                <Text as="label" size="2" weight="medium">
                                                    Select Email Template
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
                                                    <Select.Item value="scratch">Start from scratch</Select.Item>
                                                    <Select.Separator />
                                                    {availableTemplates.map(template => (
                                                        <Select.Item key={template.id} value={template.id}>
                                                            <Flex direction="column" gap="1" style={{ minWidth: '300px' }}>
                                                                <Text size="2" weight="medium" style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                                                                    {template.name}
                                                                </Text>
                                                                <Text size="1" color="gray" style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                                                                    {template.goal}
                                                                </Text>
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
                                                Available variables: {'{first_name}'}, {'{last_name}'}, {'{company}'}, {'{title}'},
                                                {'{event_date}'}, {'{event_time}'}, {'{hotel_name}'}, {'{hotel_address}'}, {'{calendly_link}'},
                                                {'{owner_name}'}, {'{campaign_name}'}, {'{target_cities}'}
                                            </Text>
                                        </Box>
                                        
                                        <Flex gap="3">
                                            <Button 
                                                onClick={() => api.put(`/api/campaigns/${campaignId}`, { 
                                                    email_template: emailTemplate, 
                                                    email_subject: emailSubject 
                                                })}
                                                variant="soft"
                                            >
                                                Save Template
                                            </Button>
                                            <Button 
                                                onClick={handleGenerateEmails}
                                                disabled={!emailTemplate || !emailSubject}
                                            >
                                                <EnvelopeClosedIcon />
                                                Generate {campaign.enriched_contacts} Personalized Emails
                                            </Button>
                                        </Flex>
                                    </Flex>
                                ) : campaign.status === 'generating_emails' ? (
                                    <Flex direction="column" align="center" justify="center" style={{ minHeight: '400px' }}>
                                        <ReloadIcon style={{ width: '48px', height: '48px', animation: 'spin 1s linear infinite' }} />
                                        <Text size="2" color="gray" mt="4">
                                            This may take a few minutes. You can navigate away and come back.
                                        </Text>
                                    </Flex>
                                ) : campaign.emails_generated > 0 ? (
                                    <Box>
                                        <Callout.Root color="green" mb="4">
                                            <Callout.Icon>
                                                <CheckIcon />
                                            </Callout.Icon>
                                            <Callout.Text>
                                                Successfully generated {campaign.emails_generated} personalized emails. 
                                                Review them in the Contacts tab.
                                            </Callout.Text>
                                        </Callout.Root>
                                        
                                        <Box p="4" style={{ backgroundColor: 'var(--gray-2)', borderRadius: '8px' }}>
                                            <Text size="2" weight="medium" mb="2">Current Email Template:</Text>
                                            <Box mb="3">
                                                <Text size="2" color="gray">Subject:</Text>
                                                <Text size="3">{campaign.email_subject || emailSubject}</Text>
                                            </Box>
                                            <Box>
                                                <Text size="2" color="gray">Template:</Text>
                                                <Text size="2" style={{ whiteSpace: 'pre-wrap' }}>
                                                    {campaign.email_template || emailTemplate}
                                                </Text>
                                            </Box>
                                        </Box>
                                        
                                        <Button 
                                            mt="4"
                                            onClick={() => navigate(`/campaigns/${campaignId}`)}
                                        >
                                            Go to Contacts Tab to Review
                                        </Button>
                                    </Box>
                                ) : (
                                    <Callout.Root color="gray">
                                        <Callout.Icon>
                                            <InfoCircledIcon />
                                        </Callout.Icon>
                                        <Callout.Text>
                                            Please complete contact enrichment before generating emails.
                                        </Callout.Text>
                                    </Callout.Root>
                                )}
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
                                                        
                                                        {/* Hotel Marker */}
                                                        {hotelCoords && campaign.event_type === 'in_person' && (
                                                            <Marker 
                                                                position={hotelCoords} 
                                                                icon={hotelIcon}
                                                            >
                                                                <Popup>
                                                                    <Box>
                                                                        <Text weight="bold">{campaign.hotel_name || 'Event Hotel'}</Text>
                                                                        <br />
                                                                        <Text size="1">{campaign.hotel_address}</Text>
                                                                    </Box>
                                                                </Popup>
                                                            </Marker>
                                                        )}
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
                
                {/* Contact Edit Dialog */}
                <Dialog.Root open={isEditingContact} onOpenChange={setIsEditingContact}>
                    <Dialog.Content style={{ maxWidth: 600 }}>
                        <Dialog.Title>Edit Contact</Dialog.Title>
                        {editingContactData && (
                            <Box mt="4">
                                <Flex direction="column" gap="3">
                                    <Flex gap="3">
                                        <Box style={{ flex: 1 }}>
                                            <Text as="label" size="2">First Name</Text>
                                            <TextField.Root
                                                value={editingContactData.first_name || ''}
                                                onChange={(e) => setEditingContactData({
                                                    ...editingContactData,
                                                    first_name: e.target.value
                                                })}
                                            />
                                        </Box>
                                        <Box style={{ flex: 1 }}>
                                            <Text as="label" size="2">Last Name</Text>
                                            <TextField.Root
                                                value={editingContactData.last_name || ''}
                                                onChange={(e) => setEditingContactData({
                                                    ...editingContactData,
                                                    last_name: e.target.value
                                                })}
                                            />
                                        </Box>
                                    </Flex>
                                    
                                    <Box>
                                        <Text as="label" size="2">Email</Text>
                                        <TextField.Root
                                            value={editingContactData.email || ''}
                                            onChange={(e) => setEditingContactData({
                                                ...editingContactData,
                                                email: e.target.value
                                            })}
                                        />
                                    </Box>
                                    
                                    <Box>
                                        <Text as="label" size="2">Phone</Text>
                                        <TextField.Root
                                            value={editingContactData.phone || ''}
                                            onChange={(e) => setEditingContactData({
                                                ...editingContactData,
                                                phone: e.target.value
                                            })}
                                        />
                                    </Box>
                                    
                                    <Box>
                                        <Text as="label" size="2">Company</Text>
                                        <TextField.Root
                                            value={editingContactData.company || ''}
                                            onChange={(e) => setEditingContactData({
                                                ...editingContactData,
                                                company: e.target.value
                                            })}
                                        />
                                    </Box>
                                    
                                    <Box>
                                        <Text as="label" size="2">Title</Text>
                                        <TextField.Root
                                            value={editingContactData.title || ''}
                                            onChange={(e) => setEditingContactData({
                                                ...editingContactData,
                                                title: e.target.value
                                            })}
                                        />
                                    </Box>
                                    
                                    <Box>
                                        <Text as="label" size="2">Neighborhood</Text>
                                        <TextField.Root
                                            value={editingContactData.neighborhood || ''}
                                            onChange={(e) => setEditingContactData({
                                                ...editingContactData,
                                                neighborhood: e.target.value
                                            })}
                                        />
                                    </Box>
                                    
                                    <Flex gap="3" mt="4" justify="end">
                                        <Dialog.Close>
                                            <Button variant="soft">Cancel</Button>
                                        </Dialog.Close>
                                        <Button 
                                            onClick={async () => {
                                                await handleUpdateContact(editingContactData.id, editingContactData);
                                                setIsEditingContact(false);
                                                setEditingContactData(null);
                                                setExpandedContactId(null);
                                            }}
                                        >
                                            Save Changes
                                        </Button>
                                    </Flex>
                                </Flex>
                            </Box>
                        )}
                    </Dialog.Content>
                </Dialog.Root>
                
                {/* Bulk Edit Modal */}
                <Dialog.Root open={showBulkEditModal} onOpenChange={setShowBulkEditModal}>
                    <Dialog.Content style={{ maxWidth: 500 }}>
                        <Dialog.Title>Bulk Edit {selectedContacts.size} Contacts</Dialog.Title>
                        <Box mt="4">
                            <Flex direction="column" gap="3">
                                <Box>
                                    <Text as="label" size="2">Field to Edit</Text>
                                    <Select.Root value={bulkEditField} onValueChange={setBulkEditField}>
                                        <Select.Trigger placeholder="Select a field..." />
                                        <Select.Content>
                                            <Select.Item value="company">Company</Select.Item>
                                            <Select.Item value="title">Title</Select.Item>
                                            <Select.Item value="neighborhood">Neighborhood</Select.Item>
                                            <Select.Item value="excluded">Excluded Status</Select.Item>
                                        </Select.Content>
                                    </Select.Root>
                                </Box>
                                
                                {bulkEditField && bulkEditField !== 'excluded' && (
                                    <Box>
                                        <Text as="label" size="2">New Value</Text>
                                        <TextField.Root
                                            value={bulkEditValue}
                                            onChange={(e) => setBulkEditValue(e.target.value)}
                                            placeholder={`Enter new ${bulkEditField}...`}
                                        />
                                    </Box>
                                )}
                                
                                {bulkEditField === 'excluded' && (
                                    <Box>
                                        <Text as="label" size="2">Excluded Status</Text>
                                        <Select.Root value={bulkEditValue} onValueChange={setBulkEditValue}>
                                            <Select.Trigger />
                                            <Select.Content>
                                                <Select.Item value="true">Exclude from Campaign</Select.Item>
                                                <Select.Item value="false">Include in Campaign</Select.Item>
                                            </Select.Content>
                                        </Select.Root>
                                    </Box>
                                )}
                                
                                <Callout.Root color="blue">
                                    <Callout.Icon>
                                        <InfoCircledIcon />
                                    </Callout.Icon>
                                    <Callout.Text>
                                        This will update the selected field for all {selectedContacts.size} selected contacts.
                                    </Callout.Text>
                                </Callout.Root>
                                
                                <Flex gap="3" justify="end">
                                    <Dialog.Close>
                                        <Button variant="soft">Cancel</Button>
                                    </Dialog.Close>
                                    <Button 
                                        onClick={handleBulkEdit}
                                        disabled={!bulkEditField || (!bulkEditValue && bulkEditField !== 'excluded')}
                                    >
                                        Update {selectedContacts.size} Contacts
                                    </Button>
                                </Flex>
                            </Flex>
                        </Box>
                    </Dialog.Content>
                </Dialog.Root>
            </Box>
        </MainLayout>
    );
};

export default CampaignDetailPage; 