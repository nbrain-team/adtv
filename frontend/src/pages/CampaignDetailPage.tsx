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
    DownloadIcon, ReloadIcon, PlusIcon, FileTextIcon
} from '@radix-ui/react-icons';
import { MainLayout } from '../components/MainLayout';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import api from '../api';
import { MapContainer, TileLayer, CircleMarker, Popup, Marker } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import React from 'react'; // Added for React.Fragment
import { GeneratorWorkflow } from '../components/GeneratorWorkflow';
import { ContactDataManager } from '../components/ContactDataManager';
import { CreateCommunicationsTab } from '../components/CreateCommunicationsTab';
import { RSVPAgreementModal } from '../components/RSVPAgreementModal';

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
    video_link?: string;
    event_link?: string;
    city?: string;
    state?: string;
    launch_date: string;
    event_type: 'virtual' | 'in_person';
    event_date: string;
    event_times?: string[];
    event_slots?: Array<{
        date: string;
        time: string;
        calendly_link?: string;
    }>;
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
    email_template?: string;
    email_subject?: string;
    created_at: string;
    updated_at: string;
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
    state?: string;
    geocoded_address?: string;
    enriched_company?: string;
    enriched_title?: string;
    enriched_phone?: string;
    enriched_linkedin?: string;
    enriched_website?: string;
    enriched_industry?: string;
    enriched_company_size?: string;
    enriched_location?: string;
    enrichment_status?: string;
    enrichment_error?: string;
    email_status?: string;
    email_sent_at?: string;
    excluded?: boolean;
    manually_edited?: boolean;
    personalized_email?: string;
    personalized_subject?: string;
    is_rsvp?: boolean;
    rsvp_status?: string;
    rsvp_date?: string;
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

// Get the best available location for a contact (prioritizing enriched data)
const getBestContactLocation = (contact: Contact): string | null => {
    // Priority order:
    // 1. geocoded_address - most accurate if available from enrichment
    // 2. enriched_location - enriched location data
    // 3. neighborhood + state - combine if both available
    // 4. neighborhood alone - original data
    
    if (contact.geocoded_address) {
        return contact.geocoded_address;
    }
    
    if (contact.enriched_location) {
        return contact.enriched_location;
    }
    
    if (contact.neighborhood && contact.state) {
        return `${contact.neighborhood}, ${contact.state}`;
    }
    
    if (contact.neighborhood) {
        return contact.neighborhood;
    }
    
    return null;
};

// Parse coordinates from geocoded address format (if stored as lat,lng)
const parseGeocodedCoords = (geocoded: string): [number, number] | null => {
    // Check if the geocoded address contains coordinates in format "lat,lng"
    const coordPattern = /^-?\d+\.?\d*,-?\d+\.?\d*$/;
    if (coordPattern.test(geocoded.trim())) {
        const [lat, lng] = geocoded.split(',').map(s => parseFloat(s.trim()));
        if (!isNaN(lat) && !isNaN(lng)) {
            return [lat, lng];
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
    const [previewContact, setPreviewContact] = useState<any>(null);
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
    
    // Pagination state for contacts
    const [currentPage, setCurrentPage] = useState(1);
    const [contactsPerPage] = useState(50);
    
    // Map state for geocoded contacts
    const [geocodedContacts, setGeocodedContacts] = useState<Map<string, [number, number]>>(new Map());
    const [isGeocodingContacts, setIsGeocodingContacts] = useState(false);
    
    // RSVP Management
    const [rsvpContacts, setRsvpContacts] = useState<Contact[]>([]);
    const [showSendCommunicationModal, setShowSendCommunicationModal] = useState(false);
    const [selectedRsvpTemplateId, setSelectedRsvpTemplateId] = useState<string>('');
    const [showRsvpCommunicationModal, setShowRsvpCommunicationModal] = useState(false);
    const [showAgreementModal, setShowAgreementModal] = useState(false);

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

    // Geocode enhanced contact addresses
    useEffect(() => {
        const geocodeEnhancedContacts = async () => {
            if (contacts.length === 0 || isGeocodingContacts) return;
            
            setIsGeocodingContacts(true);
            const newGeocodedContacts = new Map(geocodedContacts);
            
            // Process contacts with enhanced location data
            const contactsToGeocode = contacts.filter(contact => {
                const location = getBestContactLocation(contact);
                if (!location) return false;
                
                // Skip if already geocoded
                if (newGeocodedContacts.has(contact.id)) return false;
                
                // Skip if we can get coordinates from hardcoded list
                if (getNeighborhoodCoords(location)) return false;
                
                // Check if geocoded_address contains coordinates directly
                if (contact.geocoded_address && parseGeocodedCoords(contact.geocoded_address)) return false;
                
                // This contact needs geocoding
                return contact.enriched_location || contact.geocoded_address;
            });
            
            // Limit to batch geocoding to avoid overwhelming the geocoding service
            const batchSize = 10;
            for (let i = 0; i < Math.min(contactsToGeocode.length, batchSize); i++) {
                const contact = contactsToGeocode[i];
                const location = getBestContactLocation(contact);
                
                if (location) {
                    // Check if geocoded_address contains coordinates
                    if (contact.geocoded_address) {
                        const coords = parseGeocodedCoords(contact.geocoded_address);
                        if (coords) {
                            newGeocodedContacts.set(contact.id, coords);
                            continue;
                        }
                    }
                    
                    // Try to geocode the address
                    const coords = await geocodeAddress(location);
                    if (coords) {
                        newGeocodedContacts.set(contact.id, coords);
                    }
                    
                    // Small delay to avoid rate limiting
                    await new Promise(resolve => setTimeout(resolve, 200));
                }
            }
            
            setGeocodedContacts(newGeocodedContacts);
            setIsGeocodingContacts(false);
        };
        
        // Run geocoding when contacts change or after enrichment completes
        if (contacts.some(c => c.enriched_location || c.geocoded_address)) {
            geocodeEnhancedContacts();
        }
    }, [contacts, campaign?.status]); // Re-run when contacts update or campaign status changes

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
            // Fetch ALL contacts using the fetch_all parameter
            const response = await api.get(`/api/campaigns/${campaignId}/contacts?fetch_all=true`);
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
                owner_name: editedCampaign.owner_name,
                owner_email: editedCampaign.owner_email,
                owner_phone: editedCampaign.owner_phone,
                video_link: editedCampaign.video_link,
                event_link: editedCampaign.event_link,
                city: editedCampaign.city,
                state: editedCampaign.state,
                launch_date: editedCampaign.launch_date,
                event_type: editedCampaign.event_type,
                event_date: editedCampaign.event_date,
                event_times: editedCampaign.event_times,
                event_slots: editedCampaign.event_slots,
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
        if (!bulkEditField || bulkEditValue === '') return;
        
        try {
            const contactIds = Array.from(selectedContacts);
            const updates: any = {};
            updates[bulkEditField] = bulkEditValue;
            
            await api.put(`/api/campaigns/${campaignId}/contacts/bulk`, {
                contact_ids: contactIds,
                updates
            });
            
            await fetchContacts();
            setShowBulkEditModal(false);
            setBulkEditField('');
            setBulkEditValue('');
            setSelectedContacts(new Set());
        } catch (err) {
            console.error('Failed to bulk edit contacts:', err);
        }
    };
    
    // RSVP Management Functions
    const handleMoveToRSVP = async () => {
        try {
            const contactIds = Array.from(selectedContacts);
            await api.post(`/api/campaigns/${campaignId}/contacts/rsvp`, {
                contact_ids: contactIds,
                is_rsvp: true
            });
            await fetchContacts();
            setSelectedContacts(new Set());
        } catch (err) {
            console.error('Failed to move contacts to RSVP:', err);
        }
    };
    
    const handleUpdateRSVPStatus = async (contactId: string, status: string) => {
        try {
            await api.put(`/api/campaigns/${campaignId}/contacts/${contactId}/rsvp-status`, {
                rsvp_status: status
            });
            await fetchContacts();
        } catch (err) {
            console.error('Failed to update RSVP status:', err);
        }
    };
    
    const handleSendCommunication = async () => {
        if (!selectedRsvpTemplateId) return;
        
        try {
            const contactIds = selectedContacts.size > 0 ? Array.from(selectedContacts) : undefined;
            await api.post(`/api/campaigns/${campaignId}/send-communication`, {
                template_id: selectedRsvpTemplateId,
                contact_ids: contactIds
            });
            
            setShowSendCommunicationModal(false);
            setSelectedRsvpTemplateId('');
            setSelectedContacts(new Set());
        } catch (err) {
            console.error('Failed to send communication:', err);
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
        if (contact.is_rsvp) return false; // Don't show RSVP contacts in main list
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
    
    const filteredRsvpContacts = contacts.filter(contact => {
        if (!contact.is_rsvp) return false;
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
    
    // Calculate pagination
    const indexOfLastContact = currentPage * contactsPerPage;
    const indexOfFirstContact = indexOfLastContact - contactsPerPage;
    const currentContacts = filteredContacts.slice(indexOfFirstContact, indexOfLastContact);
    const totalPages = Math.ceil(filteredContacts.length / contactsPerPage);

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
                            <Tabs.Trigger value="rsvp">RSVPs ({contacts.filter(c => c.is_rsvp).length})</Tabs.Trigger>
                            <Tabs.Trigger value="create-communications">
                                Create Communications
                            </Tabs.Trigger>
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

                                        {/* Event Type (Read-only in edit mode) */}
                                        <Box>
                                            <Text size="2" weight="bold" style={{ color: 'var(--gray-12)' }}>Event Type: </Text>
                                            <Text size="2" style={{ color: 'var(--gray-12)' }}>
                                                {campaign.event_type === 'in_person' ? 'In-Person' : 'Virtual'}
                                            </Text>
                                        </Box>

                                        {/* Associate Producer Info */}
                                        <Box>
                                            <Text size="2" weight="bold" style={{ color: 'var(--gray-12)' }}>Associate Producer: </Text>
                                            {!isEditingCampaign ? (
                                                <Text size="2" style={{ color: 'var(--gray-12)' }}>
                                                    {campaign.owner_name}
                                                </Text>
                                            ) : (
                                                <TextField.Root
                                                    value={editedCampaign?.owner_name || ''}
                                                    onChange={(e) => setEditedCampaign({
                                                        ...editedCampaign!,
                                                        owner_name: e.target.value
                                                    })}
                                                    placeholder="Producer Name"
                                                    style={{ marginTop: '0.25rem' }}
                                                />
                                            )}
                                        </Box>

                                        <Box>
                                            <Text size="2" weight="bold" style={{ color: 'var(--gray-12)' }}>Associate Email: </Text>
                                            {!isEditingCampaign ? (
                                                <Text size="2" style={{ color: 'var(--gray-12)' }}>
                                                    {campaign.owner_email}
                                                </Text>
                                            ) : (
                                                <TextField.Root
                                                    value={editedCampaign?.owner_email || ''}
                                                    onChange={(e) => setEditedCampaign({
                                                        ...editedCampaign!,
                                                        owner_email: e.target.value
                                                    })}
                                                    placeholder="email@example.com"
                                                    style={{ marginTop: '0.25rem' }}
                                                />
                                            )}
                                        </Box>

                                        <Box>
                                            <Text size="2" weight="bold" style={{ color: 'var(--gray-12)' }}>Associate Phone: </Text>
                                            {!isEditingCampaign ? (
                                                <Text size="2" style={{ color: 'var(--gray-12)' }}>
                                                    {campaign.owner_phone || '-'}
                                                </Text>
                                            ) : (
                                                <TextField.Root
                                                    value={editedCampaign?.owner_phone || ''}
                                                    onChange={(e) => setEditedCampaign({
                                                        ...editedCampaign!,
                                                        owner_phone: e.target.value
                                                    })}
                                                    placeholder="(555) 123-4567"
                                                    style={{ marginTop: '0.25rem' }}
                                                />
                                            )}
                                        </Box>

                                        {/* Location Info */}
                                        <Box>
                                            <Text size="2" weight="bold" style={{ color: 'var(--gray-12)' }}>City: </Text>
                                            {!isEditingCampaign ? (
                                                <Text size="2" style={{ color: 'var(--gray-12)' }}>
                                                    {campaign.city || '-'}
                                                </Text>
                                            ) : (
                                                <TextField.Root
                                                    value={editedCampaign?.city || ''}
                                                    onChange={(e) => setEditedCampaign({
                                                        ...editedCampaign!,
                                                        city: e.target.value
                                                    })}
                                                    placeholder="City Name"
                                                    style={{ marginTop: '0.25rem' }}
                                                />
                                            )}
                                        </Box>

                                        <Box>
                                            <Text size="2" weight="bold" style={{ color: 'var(--gray-12)' }}>State: </Text>
                                            {!isEditingCampaign ? (
                                                <Text size="2" style={{ color: 'var(--gray-12)' }}>
                                                    {campaign.state || '-'}
                                                </Text>
                                            ) : (
                                                <TextField.Root
                                                    value={editedCampaign?.state || ''}
                                                    onChange={(e) => setEditedCampaign({
                                                        ...editedCampaign!,
                                                        state: e.target.value
                                                    })}
                                                    placeholder="State"
                                                    style={{ marginTop: '0.25rem' }}
                                                />
                                            )}
                                        </Box>

                                        {/* Links */}
                                        <Box>
                                            <Text size="2" weight="bold" style={{ color: 'var(--gray-12)' }}>Video Link: </Text>
                                            {!isEditingCampaign ? (
                                                <Text size="2" style={{ color: 'var(--gray-12)' }}>
                                                    {campaign.video_link || '-'}
                                                </Text>
                                            ) : (
                                                <TextField.Root
                                                    value={editedCampaign?.video_link || ''}
                                                    onChange={(e) => setEditedCampaign({
                                                        ...editedCampaign!,
                                                        video_link: e.target.value
                                                    })}
                                                    placeholder="https://..."
                                                    style={{ marginTop: '0.25rem' }}
                                                />
                                            )}
                                        </Box>

                                        <Box>
                                            <Text size="2" weight="bold" style={{ color: 'var(--gray-12)' }}>Event Link: </Text>
                                            {!isEditingCampaign ? (
                                                <Text size="2" style={{ color: 'var(--gray-12)' }}>
                                                    {campaign.event_link || '-'}
                                                </Text>
                                            ) : (
                                                <TextField.Root
                                                    value={editedCampaign?.event_link || ''}
                                                    onChange={(e) => setEditedCampaign({
                                                        ...editedCampaign!,
                                                        event_link: e.target.value
                                                    })}
                                                    placeholder="https://..."
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

                                        {/* Event Dates/Times - Conditional based on event type */}
                                        {campaign.event_type === 'in_person' ? (
                                            <>
                                                {/* In-Person Event Slots */}
                                                <Box>
                                                    <Text size="2" weight="bold" style={{ color: 'var(--gray-12)' }}>Event Date 1: </Text>
                                                    {!isEditingCampaign ? (
                                                        <Text size="2" style={{ color: 'var(--gray-12)' }}>
                                                            {campaign.event_slots?.[0]?.date ? new Date(campaign.event_slots[0].date).toLocaleDateString() : '-'}
                                                        </Text>
                                                    ) : (
                                                        <input
                                                            type="date"
                                                            value={editedCampaign?.event_slots?.[0]?.date ? 
                                                                new Date(editedCampaign.event_slots[0].date).toISOString().split('T')[0] : ''
                                                            }
                                                            onChange={(e) => {
                                                                const slots = [...(editedCampaign?.event_slots || [])];
                                                                if (!slots[0]) slots[0] = { date: '', time: '', calendly_link: '' };
                                                                slots[0].date = e.target.value;
                                                                setEditedCampaign({
                                                                    ...editedCampaign!,
                                                                    event_slots: slots
                                                                });
                                                            }}
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

                                                <Box>
                                                    <Text size="2" weight="bold" style={{ color: 'var(--gray-12)' }}>Event Time 1: </Text>
                                                    {!isEditingCampaign ? (
                                                        <Text size="2" style={{ color: 'var(--gray-12)' }}>
                                                            {campaign.event_slots?.[0]?.time || '-'}
                                                        </Text>
                                                    ) : (
                                                        <TextField.Root
                                                            value={editedCampaign?.event_slots?.[0]?.time || ''}
                                                            onChange={(e) => {
                                                                const slots = [...(editedCampaign?.event_slots || [])];
                                                                if (!slots[0]) slots[0] = { date: '', time: '', calendly_link: '' };
                                                                slots[0].time = e.target.value;
                                                                setEditedCampaign({
                                                                    ...editedCampaign!,
                                                                    event_slots: slots
                                                                });
                                                            }}
                                                            placeholder="10:00 AM"
                                                            style={{ marginTop: '0.25rem' }}
                                                        />
                                                    )}
                                                </Box>

                                                <Box>
                                                    <Text size="2" weight="bold" style={{ color: 'var(--gray-12)' }}>Event Date 2 (Optional): </Text>
                                                    {!isEditingCampaign ? (
                                                        <Text size="2" style={{ color: 'var(--gray-12)' }}>
                                                            {campaign.event_slots?.[1]?.date ? new Date(campaign.event_slots[1].date).toLocaleDateString() : '-'}
                                                        </Text>
                                                    ) : (
                                                        <input
                                                            type="date"
                                                            value={editedCampaign?.event_slots?.[1]?.date ? 
                                                                new Date(editedCampaign.event_slots[1].date).toISOString().split('T')[0] : ''
                                                            }
                                                            onChange={(e) => {
                                                                const slots = [...(editedCampaign?.event_slots || [])];
                                                                if (!slots[1]) slots[1] = { date: '', time: '', calendly_link: '' };
                                                                slots[1].date = e.target.value;
                                                                setEditedCampaign({
                                                                    ...editedCampaign!,
                                                                    event_slots: slots
                                                                });
                                                            }}
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

                                                <Box>
                                                    <Text size="2" weight="bold" style={{ color: 'var(--gray-12)' }}>Event Time 2 (Optional): </Text>
                                                    {!isEditingCampaign ? (
                                                        <Text size="2" style={{ color: 'var(--gray-12)' }}>
                                                            {campaign.event_slots?.[1]?.time || '-'}
                                                        </Text>
                                                    ) : (
                                                        <TextField.Root
                                                            value={editedCampaign?.event_slots?.[1]?.time || ''}
                                                            onChange={(e) => {
                                                                const slots = [...(editedCampaign?.event_slots || [])];
                                                                if (!slots[1]) slots[1] = { date: '', time: '', calendly_link: '' };
                                                                slots[1].time = e.target.value;
                                                                setEditedCampaign({
                                                                    ...editedCampaign!,
                                                                    event_slots: slots
                                                                });
                                                            }}
                                                            placeholder="2:00 PM"
                                                            style={{ marginTop: '0.25rem' }}
                                                        />
                                                    )}
                                                </Box>

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
                                                            placeholder="Hotel Name"
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
                                                            placeholder="123 Main St, City, State ZIP"
                                                            style={{ marginTop: '0.25rem' }}
                                                        />
                                                    )}
                                                </Box>

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
                                                            placeholder="https://calendly.com/..."
                                                            style={{ marginTop: '0.25rem' }}
                                                        />
                                                    )}
                                                </Box>
                                            </>
                                        ) : (
                                            <>
                                                {/* Virtual Event Slots */}
                                                {[0, 1, 2].map((index) => (
                                                    <React.Fragment key={index}>
                                                        <Box>
                                                            <Text size="2" weight="bold" style={{ color: 'var(--gray-12)' }}>
                                                                Event Date {index + 1}{index > 0 ? ' (Optional)' : ''}: 
                                                            </Text>
                                                            {!isEditingCampaign ? (
                                                                <Text size="2" style={{ color: 'var(--gray-12)' }}>
                                                                    {campaign.event_slots?.[index]?.date ? 
                                                                        new Date(campaign.event_slots[index].date).toLocaleDateString() : '-'}
                                                                </Text>
                                                            ) : (
                                                                <input
                                                                    type="date"
                                                                    value={editedCampaign?.event_slots?.[index]?.date ? 
                                                                        new Date(editedCampaign.event_slots[index].date).toISOString().split('T')[0] : ''
                                                                    }
                                                                    onChange={(e) => {
                                                                        const slots = [...(editedCampaign?.event_slots || [])];
                                                                        if (!slots[index]) slots[index] = { date: '', time: '', calendly_link: '' };
                                                                        slots[index].date = e.target.value;
                                                                        setEditedCampaign({
                                                                            ...editedCampaign!,
                                                                            event_slots: slots
                                                                        });
                                                                    }}
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

                                                        <Box>
                                                            <Text size="2" weight="bold" style={{ color: 'var(--gray-12)' }}>
                                                                Event Time {index + 1}{index > 0 ? ' (Optional)' : ''}: 
                                                            </Text>
                                                            {!isEditingCampaign ? (
                                                                <Text size="2" style={{ color: 'var(--gray-12)' }}>
                                                                    {campaign.event_slots?.[index]?.time || '-'}
                                                                </Text>
                                                            ) : (
                                                                <TextField.Root
                                                                    value={editedCampaign?.event_slots?.[index]?.time || ''}
                                                                    onChange={(e) => {
                                                                        const slots = [...(editedCampaign?.event_slots || [])];
                                                                        if (!slots[index]) slots[index] = { date: '', time: '', calendly_link: '' };
                                                                        slots[index].time = e.target.value;
                                                                        setEditedCampaign({
                                                                            ...editedCampaign!,
                                                                            event_slots: slots
                                                                        });
                                                                    }}
                                                                    placeholder="10:00 AM"
                                                                    style={{ marginTop: '0.25rem' }}
                                                                />
                                                            )}
                                                        </Box>

                                                        <Box>
                                                            <Text size="2" weight="bold" style={{ color: 'var(--gray-12)' }}>
                                                                Calendly Link {index + 1}{index > 0 ? ' (Optional)' : ''}: 
                                                            </Text>
                                                            {!isEditingCampaign ? (
                                                                <Text size="2" style={{ color: 'var(--gray-12)' }}>
                                                                    {campaign.event_slots?.[index]?.calendly_link || '-'}
                                                                </Text>
                                                            ) : (
                                                                <TextField.Root
                                                                    value={editedCampaign?.event_slots?.[index]?.calendly_link || ''}
                                                                    onChange={(e) => {
                                                                        const slots = [...(editedCampaign?.event_slots || [])];
                                                                        if (!slots[index]) slots[index] = { date: '', time: '', calendly_link: '' };
                                                                        slots[index].calendly_link = e.target.value;
                                                                        setEditedCampaign({
                                                                            ...editedCampaign!,
                                                                            event_slots: slots
                                                                        });
                                                                    }}
                                                                    placeholder="https://calendly.com/..."
                                                                    style={{ marginTop: '0.25rem' }}
                                                                />
                                                            )}
                                                        </Box>
                                                    </React.Fragment>
                                                ))}
                                            </>
                                        )}

                                        {/* Locations To Scrape */}
                                        <Box>
                                            <Text size="2" weight="bold" style={{ color: 'var(--gray-12)' }}>Locations To Scrape: </Text>
                                            {!isEditingCampaign ? (
                                                <Text size="2" style={{ color: 'var(--gray-12)', whiteSpace: 'pre-wrap' }}>
                                                    {campaign.target_cities || '-'}
                                                </Text>
                                            ) : (
                                                <TextArea
                                                    value={editedCampaign?.target_cities || ''}
                                                    onChange={(e) => setEditedCampaign({
                                                        ...editedCampaign!,
                                                        target_cities: e.target.value
                                                    })}
                                                    placeholder="Enter locations, one per line"
                                                    rows={3}
                                                    style={{ marginTop: '0.25rem' }}
                                                />
                                            )}
                                        </Box>
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
                                        {console.log('Campaign total_contacts:', campaign.total_contacts)}
                                        {console.log('Should show upload button:', campaign.status === 'draft' || campaign.total_contacts === 0)}
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
                                    
                                    {(() => {
                                        // Get all non-excluded contacts
                                        const allContacts = contacts.filter(c => !c.excluded);
                                        
                                        // Get coordinates for each contact using enhanced data
                                        const contactsWithCoords = allContacts
                                            .map(contact => {
                                                const location = getBestContactLocation(contact);
                                                let coords = null;
                                                
                                                // Priority for getting coordinates:
                                                // 1. Check if we have geocoded coordinates in state
                                                if (geocodedContacts.has(contact.id)) {
                                                    coords = geocodedContacts.get(contact.id);
                                                }
                                                // 2. Check if geocoded_address has coordinates
                                                else if (contact.geocoded_address) {
                                                    coords = parseGeocodedCoords(contact.geocoded_address);
                                                }
                                                // 3. Try hardcoded neighborhood coords
                                                else if (location) {
                                                    coords = getNeighborhoodCoords(location);
                                                }
                                                
                                                return {
                                                    ...contact,
                                                    location,
                                                    coords
                                                };
                                            })
                                            .filter(c => c.coords !== null);
                                        
                                        const contactsWithoutCoords = allContacts.filter(contact => {
                                            const location = getBestContactLocation(contact);
                                            if (!location) return true;
                                            
                                            // Check all possible coordinate sources
                                            if (geocodedContacts.has(contact.id)) return false;
                                            if (contact.geocoded_address && parseGeocodedCoords(contact.geocoded_address)) return false;
                                            if (getNeighborhoodCoords(location)) return false;
                                            
                                            return true;
                                        });
                                        
                                        // Count locations for mapped contacts
                                        const locationCounts = contactsWithCoords.reduce((acc, contact) => {
                                            const key = contact.location || 'Unknown';
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
                                                    {isGeocodingContacts && (
                                                        <Badge size="1" color="blue">
                                                            Geocoding enhanced locations...
                                                        </Badge>
                                                    )}
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
                                                            
                                                            {Object.entries(locationCounts).map(([location, count]) => {
                                                                // Find the first contact with this location to get coords
                                                                const contactWithLocation = contactsWithCoords.find(c => c.location === location);
                                                                const coords = contactWithLocation?.coords;
                                                                if (!coords) return null;
                                                                
                                                                return (
                                                                    <CircleMarker
                                                                        key={location}
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
                                                                                <Text weight="bold">{location}</Text>
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
                                </Card>
                            </Box>
                        </Tabs.Content>

                        {/* Contacts Tab */}
                        <Tabs.Content value="contacts">
                            <Card>
                                <Flex align="center" justify="between" mb="4">
                                    <Heading size="4">Contact List ({filteredContacts.length} total)</Heading>
                                    <Flex gap="3" align="center">
                                        <TextField.Root
                                            placeholder="Search contacts..."
                                            value={searchTerm}
                                            onChange={(e) => {
                                                setSearchTerm(e.target.value);
                                                setCurrentPage(1); // Reset to first page on search
                                            }}
                                            style={{ width: '300px' }}
                                        >
                                            <TextField.Slot>
                                                <MagnifyingGlassIcon />
                                            </TextField.Slot>
                                        </TextField.Root>
                                        
                                        {selectedContacts.size > 0 && (
                                            <>
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
                                                        <DropdownMenu.Item onClick={handleMoveToRSVP}>
                                                            <CheckIcon style={{ marginRight: '8px' }} />
                                                            Move to RSVP
                                                        </DropdownMenu.Item>
                                                        <DropdownMenu.Separator />
                                                        <DropdownMenu.Item onClick={() => setShowBulkEditModal(true)}>
                                                            <Pencil1Icon style={{ marginRight: '8px' }} />
                                                            Bulk Edit
                                                        </DropdownMenu.Item>
                                                    </DropdownMenu.Content>
                                                </DropdownMenu.Root>
                                            </>
                                        )}
                                    </Flex>
                                </Flex>

                                {/* Add Contact Data Manager for export/import */}
                                {campaign.total_contacts > 0 && (
                                    <Box mb="4">
                                        <ContactDataManager 
                                            campaignId={campaignId!} 
                                            campaignName={campaign.name}
                                        />
                                    </Box>
                                )}

                                <Box style={{ overflowX: 'auto' }}>
                                    <Table.Root style={{ minWidth: '1200px' }}>
                                        <Table.Header>
                                            <Table.Row>
                                                <Table.Cell style={{ position: 'sticky', left: 0, backgroundColor: 'var(--color-background)', zIndex: 1 }}>
                                                    <Checkbox
                                                        checked={selectedContacts.size === currentContacts.length && currentContacts.length > 0}
                                                        onCheckedChange={() => {
                                                            if (selectedContacts.size === currentContacts.length) {
                                                                // Deselect all on current page
                                                                const newSelection = new Set(selectedContacts);
                                                                currentContacts.forEach(c => newSelection.delete(c.id));
                                                                setSelectedContacts(newSelection);
                                                            } else {
                                                                // Select all on current page
                                                                const newSelection = new Set(selectedContacts);
                                                                currentContacts.forEach(c => newSelection.add(c.id));
                                                                setSelectedContacts(newSelection);
                                                            }
                                                        }}
                                                    />
                                                </Table.Cell>
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
                                            {currentContacts.map(contact => (
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

                                {/* Pagination Controls */}
                                {totalPages > 1 && (
                                    <Flex align="center" justify="between" mt="4" pt="4" style={{ borderTop: '1px solid var(--gray-4)' }}>
                                        <Text size="2" color="gray">
                                            Showing {indexOfFirstContact + 1}-{Math.min(indexOfLastContact, filteredContacts.length)} of {filteredContacts.length} contacts
                                        </Text>
                                        
                                        <Flex gap="2" align="center">
                                            <Button 
                                                variant="soft" 
                                                size="2"
                                                disabled={currentPage === 1}
                                                onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                                            >
                                                Previous
                                            </Button>
                                            
                                            {/* Page numbers */}
                                            <Flex gap="1">
                                                {[...Array(Math.min(10, totalPages))].map((_, index) => {
                                                    let pageNum;
                                                    if (totalPages <= 10) {
                                                        pageNum = index + 1;
                                                    } else if (currentPage <= 5) {
                                                        pageNum = index + 1;
                                                    } else if (currentPage >= totalPages - 4) {
                                                        pageNum = totalPages - 9 + index;
                                                    } else {
                                                        pageNum = currentPage - 4 + index;
                                                    }
                                                    
                                                    return (
                                                        <Button
                                                            key={index}
                                                            variant={pageNum === currentPage ? 'solid' : 'soft'}
                                                            size="2"
                                                            onClick={() => setCurrentPage(pageNum)}
                                                        >
                                                            {pageNum}
                                                        </Button>
                                                    );
                                                })}
                                            </Flex>
                                            
                                            <Button 
                                                variant="soft" 
                                                size="2"
                                                disabled={currentPage === totalPages}
                                                onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
                                            >
                                                Next
                                            </Button>
                                        </Flex>
                                    </Flex>
                                )}
                            </Card>
                        </Tabs.Content>

                        {/* RSVP Tab */}
                        <Tabs.Content value="rsvp">
                            <Card>
                                <Flex align="center" justify="between" mb="4">
                                    <Heading size="4">RSVP List</Heading>
                                    <Flex gap="3" align="center">
                                        <TextField.Root
                                            placeholder="Search RSVPs..."
                                            value={searchTerm}
                                            onChange={(e) => setSearchTerm(e.target.value)}
                                            style={{ width: '300px' }}
                                        >
                                            <TextField.Slot>
                                                <MagnifyingGlassIcon />
                                            </TextField.Slot>
                                        </TextField.Root>
                                        
                                        <Button 
                                            variant="solid"
                                            onClick={() => setShowSendCommunicationModal(true)}
                                        >
                                            <EnvelopeClosedIcon />
                                            Send Communication
                                        </Button>
                                        
                                        <Button 
                                            variant="solid"
                                            color="green"
                                            onClick={() => setShowAgreementModal(true)}
                                            disabled={selectedContacts.size === 0}
                                        >
                                            <FileTextIcon />
                                            Send Agreement ({selectedContacts.size})
                                        </Button>
                                    </Flex>
                                </Flex>

                                <Box style={{ overflowX: 'auto' }}>
                                    <Table.Root style={{ minWidth: '1200px' }}>
                                        <Table.Header>
                                            <Table.Row>
                                                <Table.ColumnHeaderCell style={{ position: 'sticky', left: 0, backgroundColor: 'var(--color-background)', zIndex: 1 }}>
                                                    <Checkbox
                                                        checked={selectedContacts.size === filteredRsvpContacts.length && filteredRsvpContacts.length > 0}
                                                        onCheckedChange={toggleAllContacts}
                                                    />
                                                </Table.ColumnHeaderCell>
                                                <Table.ColumnHeaderCell>First Name</Table.ColumnHeaderCell>
                                                <Table.ColumnHeaderCell>Last Name</Table.ColumnHeaderCell>
                                                <Table.ColumnHeaderCell>Email</Table.ColumnHeaderCell>
                                                <Table.ColumnHeaderCell>Phone</Table.ColumnHeaderCell>
                                                <Table.ColumnHeaderCell>Company</Table.ColumnHeaderCell>
                                                <Table.ColumnHeaderCell>RSVP Date</Table.ColumnHeaderCell>
                                                <Table.ColumnHeaderCell>RSVP Status</Table.ColumnHeaderCell>
                                                <Table.ColumnHeaderCell>Actions</Table.ColumnHeaderCell>
                                            </Table.Row>
                                        </Table.Header>
                                        <Table.Body>
                                            {filteredRsvpContacts.map(contact => (
                                                <Table.Row key={contact.id}>
                                                    <Table.Cell style={{ position: 'sticky', left: 0, backgroundColor: 'var(--color-background)', zIndex: 1 }}>
                                                        <Checkbox
                                                            checked={selectedContacts.has(contact.id)}
                                                            onCheckedChange={() => toggleContactSelection(contact.id)}
                                                        />
                                                    </Table.Cell>
                                                    <Table.Cell>{contact.first_name || '-'}</Table.Cell>
                                                    <Table.Cell>{contact.last_name || '-'}</Table.Cell>
                                                    <Table.Cell>{contact.email || '-'}</Table.Cell>
                                                    <Table.Cell>{contact.enriched_phone || contact.phone || '-'}</Table.Cell>
                                                    <Table.Cell>{contact.enriched_company || contact.company || '-'}</Table.Cell>
                                                    <Table.Cell>
                                                        {contact.rsvp_date ? new Date(contact.rsvp_date).toLocaleDateString() : '-'}
                                                    </Table.Cell>
                                                    <Table.Cell>
                                                        <Select.Root 
                                                            value={contact.rsvp_status || 'none'}
                                                            onValueChange={(value) => handleUpdateRSVPStatus(contact.id, value)}
                                                        >
                                                            <Select.Trigger />
                                                            <Select.Content>
                                                                <Select.Item value="none">-</Select.Item>
                                                                <Select.Item value="attended">Attended</Select.Item>
                                                                <Select.Item value="no_show">No Show</Select.Item>
                                                                <Select.Item value="signed_agreement">Signed Agreement</Select.Item>
                                                                <Select.Item value="cancelled">Cancelled</Select.Item>
                                                            </Select.Content>
                                                        </Select.Root>
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
                                                        </Flex>
                                                    </Table.Cell>
                                                </Table.Row>
                                            ))}
                                        </Table.Body>
                                    </Table.Root>
                                </Box>
                            </Card>
                        </Tabs.Content>

                        {/* Create Communications Tab */}
                        <Tabs.Content value="create-communications">
                            <CreateCommunicationsTab
                                campaignId={campaignId!}
                                campaign={campaign}
                                contacts={contacts}
                            />
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
                                    
                                    // Get coordinates for each contact using enhanced data
                                    const contactsWithCoords = allContacts
                                        .map(contact => {
                                            const location = getBestContactLocation(contact);
                                            let coords = null;
                                            
                                            // Priority for getting coordinates:
                                            // 1. Check if we have geocoded coordinates in state
                                            if (geocodedContacts.has(contact.id)) {
                                                coords = geocodedContacts.get(contact.id);
                                            }
                                            // 2. Check if geocoded_address has coordinates
                                            else if (contact.geocoded_address) {
                                                coords = parseGeocodedCoords(contact.geocoded_address);
                                            }
                                            // 3. Try hardcoded neighborhood coords
                                            else if (location) {
                                                coords = getNeighborhoodCoords(location);
                                            }
                                            
                                            return {
                                                ...contact,
                                                location,
                                                coords
                                            };
                                        })
                                        .filter(c => c.coords !== null);
                                    
                                    const contactsWithoutCoords = allContacts.filter(contact => {
                                        const location = getBestContactLocation(contact);
                                        if (!location) return true;
                                        
                                        // Check all possible coordinate sources
                                        if (geocodedContacts.has(contact.id)) return false;
                                        if (contact.geocoded_address && parseGeocodedCoords(contact.geocoded_address)) return false;
                                        if (getNeighborhoodCoords(location)) return false;
                                        
                                        return true;
                                    });
                                    
                                    // Count locations for mapped contacts
                                    const locationCounts = contactsWithCoords.reduce((acc, contact) => {
                                        const key = contact.location || 'Unknown';
                                        acc[key] = (acc[key] || 0) + 1;
                                        return acc;
                                    }, {} as Record<string, number>);
                                    
                                    // Count unmapped locations
                                    const unmappedLocations = contactsWithoutCoords.reduce((acc, contact) => {
                                        const key = getBestContactLocation(contact) || 'No location data';
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
                                                {isGeocodingContacts && (
                                                    <Badge size="2" color="blue">
                                                        Geocoding enhanced locations...
                                                    </Badge>
                                                )}
                                            </Flex>
                                            
                                            {contactsWithCoords.length === 0 ? (
                                                <Box p="4">
                                                    <Text color="gray">No contacts with valid location data to display on map.</Text>
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
                                                        
                                                        {Object.entries(locationCounts).map(([location, count]) => {
                                                            // Find the first contact with this location to get coords
                                                            const contactWithLocation = contactsWithCoords.find(c => c.location === location);
                                                            const coords = contactWithLocation?.coords;
                                                            if (!coords) return null;
                                                            
                                                            return (
                                                                <CircleMarker
                                                                    key={location}
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
                                                                            <Text weight="bold">{location}</Text>
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
                                                        <Text size="2" weight="bold" mb="2">Mapped Locations</Text>
                                                        {Object.entries(locationCounts)
                                                            .sort(([, a], [, b]) => b - a)
                                                            .map(([location, count]) => (
                                                                <Flex key={location} justify="between" gap="3" mb="1">
                                                                    <Text size="1">{location}</Text>
                                                                    <Text size="1" weight="medium">{count}</Text>
                                                                </Flex>
                                                            ))
                                                        }
                                                        
                                                        {contactsWithoutCoords.length > 0 && (
                                                            <>
                                                                <Text size="2" weight="bold" mt="3" mb="2" color="orange">
                                                                    Unmapped Locations
                                                                </Text>
                                                                <Text size="1" color="gray" mb="2">
                                                                    (Need coordinates to display on map)
                                                                </Text>
                                                                {Object.entries(unmappedLocations)
                                                                    .sort(([, a], [, b]) => b - a)
                                                                    .slice(0, 20) // Show top 20
                                                                    .map(([location, count]) => (
                                                                        <Flex key={location} justify="between" gap="3" mb="1">
                                                                            <Text size="1" color="orange">{location}</Text>
                                                                            <Text size="1" weight="medium" color="orange">{count}</Text>
                                                                        </Flex>
                                                                    ))
                                                                }
                                                                {Object.keys(unmappedLocations).length > 20 && (
                                                                    <Text size="1" color="gray" mt="2">
                                                                        ... and {Object.keys(unmappedLocations).length - 20} more
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
                    <Dialog.Content style={{ maxWidth: 450 }}>
                        <Dialog.Title>Bulk Edit Contacts</Dialog.Title>
                        <Box mt="4">
                            <Flex direction="column" gap="4">
                                <Text size="2" color="gray">
                                    Update {selectedContacts.size} selected contacts
                                </Text>
                                
                                <Box>
                                    <Text as="label" size="2" mb="1" weight="medium">
                                        Field to Update
                                    </Text>
                                    <Select.Root 
                                        value={bulkEditField}
                                        onValueChange={setBulkEditField}
                                    >
                                        <Select.Trigger placeholder="Select field..." />
                                        <Select.Content>
                                            <Select.Item value="company">Company</Select.Item>
                                            <Select.Item value="title">Title</Select.Item>
                                            <Select.Item value="neighborhood">Neighborhood</Select.Item>
                                        </Select.Content>
                                    </Select.Root>
                                </Box>
                                
                                <Box>
                                    <Text as="label" size="2" mb="1" weight="medium">
                                        New Value
                                    </Text>
                                    <TextField.Root
                                        value={bulkEditValue}
                                        onChange={(e) => setBulkEditValue(e.target.value)}
                                        placeholder="Enter new value..."
                                    />
                                </Box>
                                
                                <Flex gap="3" justify="end">
                                    <Dialog.Close>
                                        <Button variant="soft">Cancel</Button>
                                    </Dialog.Close>
                                    <Button 
                                        onClick={handleBulkEdit}
                                        disabled={!bulkEditField || !bulkEditValue}
                                    >
                                        Update Contacts
                                    </Button>
                                </Flex>
                            </Flex>
                        </Box>
                    </Dialog.Content>
                </Dialog.Root>
                
                {/* Send Communication Modal */}
                <Dialog.Root open={showSendCommunicationModal} onOpenChange={setShowSendCommunicationModal}>
                    <Dialog.Content style={{ maxWidth: 600 }}>
                        <Dialog.Title>Send Communication to RSVPs</Dialog.Title>
                        <Box mt="4">
                            <Flex direction="column" gap="4">
                                <Box>
                                    <Text size="2" mb="2">
                                        Select an email template to send to {selectedContacts.size > 0 ? selectedContacts.size : 'all'} RSVP contacts
                                    </Text>
                                </Box>
                                
                                <Box>
                                    <Text as="label" size="2" mb="1" weight="medium">
                                        Email Template
                                    </Text>
                                    <Select.Root 
                                        value={selectedRsvpTemplateId}
                                        onValueChange={setSelectedRsvpTemplateId}
                                    >
                                        <Select.Trigger placeholder="Select a template..." />
                                        <Select.Content>
                                            {availableTemplates.map(template => (
                                                <Select.Item key={template.id} value={template.id}>
                                                    {template.name}
                                                </Select.Item>
                                            ))}
                                        </Select.Content>
                                    </Select.Root>
                                </Box>
                                
                                {selectedRsvpTemplateId && (
                                    <Box>
                                        <Text size="2" weight="medium" mb="3">
                                            Email Preview (with mail merge)
                                        </Text>
                                        {(() => {
                                            const template = availableTemplates.find(t => t.id === selectedRsvpTemplateId);
                                            if (!template) return null;
                                            
                                            // Get first RSVP contact for preview
                                            const rsvpContacts = contacts.filter(c => c.is_rsvp);
                                            const firstContact = rsvpContacts.length > 0 ? rsvpContacts[0] : null;
                                            
                                            // Apply mail merge for preview
                                            let mergedSubject = template.subject;
                                            let mergedBody = template.body;
                                            
                                            if (firstContact) {
                                                // Contact-level replacements
                                                const contactReplacements = {
                                                    '{{FirstName}}': firstContact.first_name || '[FirstName]',
                                                    '{{LastName}}': firstContact.last_name || '[LastName]',
                                                    '{{Email}}': firstContact.email || '[Email]',
                                                    '{{Phone}}': firstContact.enriched_phone || firstContact.phone || '[Phone]',
                                                    '{{Company}}': firstContact.enriched_company || firstContact.company || '[Company]',
                                                    '{{Title}}': firstContact.enriched_title || firstContact.title || '[Title]',
                                                    '{{Neighborhood_1}}': firstContact.neighborhood || '[Neighborhood]',
                                                };
                                                
                                                // Campaign-level replacements
                                                const campaignReplacements = {
                                                    '[[Associate Name]]': campaign?.owner_name || '[Associate Name]',
                                                    '[[Associate email]]': campaign?.owner_email || '[Associate Email]',
                                                    '[[Associate Phone]]': campaign?.owner_phone || '[Associate Phone]',
                                                    '[[City]]': campaign?.city || '[City]',
                                                    '[[State]]': campaign?.state || '[State]',
                                                    '[[VIDEO-LINK]]': campaign?.video_link || '[Video Link]',
                                                    '[[Event-Link]]': campaign?.event_link || '[Event Link]',
                                                    '[[Hotel Name]]': campaign?.hotel_name || '[Hotel Name]',
                                                    '[[Hotel Address]]': campaign?.hotel_address || '[Hotel Address]',
                                                    '[[Date1]]': campaign?.event_slots?.[0]?.date || '[Date 1]',
                                                    '[[Time1]]': campaign?.event_slots?.[0]?.time || '[Time 1]',
                                                    '[[Date2]]': campaign?.event_slots?.[1]?.date || '',
                                                    '[[Time2]]': campaign?.event_slots?.[1]?.time || '',
                                                    '[[Date3]]': campaign?.event_slots?.[2]?.date || '',
                                                    '[[Time3]]': campaign?.event_slots?.[2]?.time || '',
                                                    '[[Calendly Link 1]]': campaign?.event_slots?.[0]?.calendly_link || '',
                                                    '[[Calendly Link 2]]': campaign?.event_slots?.[1]?.calendly_link || '',
                                                    '[[Calendly Link 3]]': campaign?.event_slots?.[2]?.calendly_link || '',
                                                };
                                                
                                                // Apply all replacements
                                                for (const [key, value] of Object.entries(contactReplacements)) {
                                                    mergedSubject = mergedSubject.replace(new RegExp(key.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'g'), value);
                                                    mergedBody = mergedBody.replace(new RegExp(key.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'g'), value);
                                                }
                                                
                                                for (const [key, value] of Object.entries(campaignReplacements)) {
                                                    mergedSubject = mergedSubject.replace(new RegExp(key.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'g'), value);
                                                    mergedBody = mergedBody.replace(new RegExp(key.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'g'), value);
                                                }
                                            }
                                            
                                            return (
                                                <Card style={{ backgroundColor: 'var(--gray-1)', padding: '1.5rem' }}>
                                                    {firstContact && (
                                                        <Box mb="3">
                                                            <Badge color="blue" size="1">
                                                                Preview for: {firstContact.first_name} {firstContact.last_name}
                                                            </Badge>
                                                        </Box>
                                                    )}
                                                    
                                                    <Box mb="3">
                                                        <Text size="1" color="gray" weight="medium">SUBJECT</Text>
                                                        <Text size="3" weight="medium" style={{ display: 'block', marginTop: '0.25rem' }}>
                                                            {mergedSubject}
                                                        </Text>
                                                    </Box>
                                                    
                                                    <Box>
                                                        <Text size="1" color="gray" weight="medium">EMAIL BODY</Text>
                                                        <ScrollArea style={{ height: '300px', marginTop: '0.5rem' }}>
                                                            <Text size="2" style={{ 
                                                                whiteSpace: 'pre-wrap',
                                                                lineHeight: '1.6',
                                                                fontFamily: 'system-ui, -apple-system, sans-serif'
                                                            }}>
                                                                {mergedBody}
                                                            </Text>
                                                        </ScrollArea>
                                                    </Box>
                                                </Card>
                                            );
                                        })()}
                                    </Box>
                                )}
                                
                                <Flex gap="3" justify="end">
                                    <Dialog.Close>
                                        <Button variant="soft">Cancel</Button>
                                    </Dialog.Close>
                                    <Button 
                                        onClick={handleSendCommunication}
                                        disabled={!selectedRsvpTemplateId}
                                    >
                                        <EnvelopeClosedIcon />
                                        Send Email
                                    </Button>
                                </Flex>
                            </Flex>
                        </Box>
                    </Dialog.Content>
                </Dialog.Root>
            </Box>
            
            {/* RSVP Agreement Modal */}
            <RSVPAgreementModal
                open={showAgreementModal}
                onOpenChange={setShowAgreementModal}
                selectedContacts={Array.from(selectedContacts).map(id => 
                    contacts.find(c => c.id === id)
                ).filter(c => c !== undefined) as Contact[]}
                campaignId={campaignId!}
                campaignName={campaign?.name || ''}
            />
        </MainLayout>
    );
};

export default CampaignDetailPage; 