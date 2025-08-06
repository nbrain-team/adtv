import React, { useState, useEffect } from 'react';
import { 
    Box, Button, Card, Flex, Heading, Text, Badge, Callout, 
    Select, Checkbox, ScrollArea, Table, Dialog, IconButton, TextField, TextArea
} from '@radix-ui/themes';
import { 
    PersonIcon, CheckCircledIcon, FileTextIcon, 
    DownloadIcon, InfoCircledIcon, Cross2Icon, ExternalLinkIcon, Pencil1Icon
} from '@radix-ui/react-icons';
import api from '../services/api';

interface Contact {
    id: string;
    first_name?: string;
    last_name?: string;
    email?: string;
    company?: string;
    title?: string;
    phone?: string;
    neighborhood?: string;
    is_rsvp?: boolean;
    enriched_phone?: string;
    enriched_company?: string;
    enriched_title?: string;
}

interface EmailTemplate {
    id: string;
    name: string;
    subject: string;
    body: string;
    template_type?: string;
}

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
    event_type: 'virtual' | 'in_person';
    event_slots?: Array<{
        date: string;
        time: string;
        calendly_link?: string;
    }>;
    hotel_name?: string;
    hotel_address?: string;
    calendly_link?: string;
}

interface CreateCommunicationsTabProps {
    campaignId: string;
    campaign: Campaign;
    contacts: Contact[];
}

interface GeneratedFile {
    id: string;
    name: string;
    contactCount: number;
    templateCount: number;
    createdAt: string;
    googleSheetUrl?: string;
}

export const CreateCommunicationsTab: React.FC<CreateCommunicationsTabProps> = ({
    campaignId,
    campaign,
    contacts
}) => {
    const [selectedContactType, setSelectedContactType] = useState<'all' | 'rsvp' | null>(null);
    const [availableTemplates, setAvailableTemplates] = useState<EmailTemplate[]>([]);
    const [selectedTemplates, setSelectedTemplates] = useState<Set<string>>(new Set());
    const [isGenerating, setIsGenerating] = useState(false);
    const [generatedFiles, setGeneratedFiles] = useState<GeneratedFile[]>([]);
    const [showPreview, setShowPreview] = useState(false);
    const [previewData, setPreviewData] = useState<any[]>([]);
    const [generationProgress, setGenerationProgress] = useState(0);
    const [showEditModal, setShowEditModal] = useState(false);
    const [editingTemplate, setEditingTemplate] = useState<EmailTemplate | null>(null);
    const [templateForm, setTemplateForm] = useState({
        name: '',
        subject: '',
        body: '',
        template_type: 'general'
    });

    useEffect(() => {
        fetchTemplates();
        loadGeneratedFiles();
    }, [campaignId]);

    const fetchTemplates = async () => {
        try {
            const response = await api.get(`/api/campaigns/${campaignId}/email-templates`);
            setAvailableTemplates(response.data);
        } catch (err) {
            console.error('Failed to fetch templates:', err);
        }
    };

    const loadGeneratedFiles = () => {
        // Load from localStorage for now
        const saved = localStorage.getItem(`campaign_${campaignId}_files`);
        if (saved) {
            setGeneratedFiles(JSON.parse(saved));
        }
    };

    const saveGeneratedFile = (file: GeneratedFile) => {
        const updated = [...generatedFiles, file];
        setGeneratedFiles(updated);
        localStorage.setItem(`campaign_${campaignId}_files`, JSON.stringify(updated));
    };

    const selectContactType = (type: 'all' | 'rsvp') => {
        setSelectedContactType(type);
        setSelectedTemplates(new Set());
    };

    const toggleTemplate = (templateId: string) => {
        const newSelection = new Set(selectedTemplates);
        if (newSelection.has(templateId)) {
            newSelection.delete(templateId);
        } else {
            newSelection.add(templateId);
        }
        setSelectedTemplates(newSelection);
    };

    const handleEditTemplate = (template: EmailTemplate) => {
        setEditingTemplate(template);
        setTemplateForm({
            name: template.name,
            subject: template.subject,
            body: template.body,
            template_type: template.template_type || 'general'
        });
        setShowEditModal(true);
    };

    const handleUpdateTemplate = async () => {
        if (!editingTemplate) return;
        
        try {
            await api.put(`/api/campaigns/${campaignId}/email-templates/${editingTemplate.id}`, templateForm);
            await fetchTemplates();
            setShowEditModal(false);
            setEditingTemplate(null);
            alert('Template updated successfully');
        } catch (err) {
            console.error('Failed to update template:', err);
            alert('Failed to update template');
        }
    };

    const applyMailMerge = (template: EmailTemplate, contact: Contact): { subject: string; body: string } => {
        let mergedSubject = template.subject;
        let mergedBody = template.body;
        
        // Contact-level replacements
        const contactReplacements: Record<string, string> = {
            '{{FirstName}}': contact.first_name || '',
            '{{LastName}}': contact.last_name || '',
            '{{Email}}': contact.email || '',
            '{{Phone}}': contact.enriched_phone || contact.phone || '',
            '{{Company}}': contact.enriched_company || contact.company || '',
            '{{Title}}': contact.enriched_title || contact.title || '',
            '{{Neighborhood_1}}': contact.neighborhood || '',
            '{{Neighborhood}}': contact.neighborhood || '',
            // Legacy lowercase versions
            '{{first_name}}': contact.first_name || '',
            '{{last_name}}': contact.last_name || '',
            '{{email}}': contact.email || '',
            '{{phone}}': contact.enriched_phone || contact.phone || '',
            '{{company}}': contact.enriched_company || contact.company || '',
            '{{title}}': contact.enriched_title || contact.title || '',
            '{{neighborhood}}': contact.neighborhood || '',
        };
        
        // Campaign-level replacements
        const campaignReplacements: Record<string, string> = {
            '[[Associate Name]]': campaign.owner_name || '',
            '[[Associate email]]': campaign.owner_email || '',
            '[[Associate Phone]]': campaign.owner_phone || '',
            '[[AssociateName]]': campaign.owner_name || '',
            '[[AssociatePhone]]': campaign.owner_phone || '',
            '[[City]]': campaign.city || '',
            '[[State]]': campaign.state || '',
            '[[VIDEO-LINK]]': campaign.video_link || '',
            '[[Event-Link]]': campaign.event_link || '',
            '[[Hotel Name]]': campaign.hotel_name || '',
            '[[Hotel Address]]': campaign.hotel_address || '',
            '[[HotelName]]': campaign.hotel_name || '',
            '[[HotelAddress]]': campaign.hotel_address || '',
            '[[Date1]]': campaign.event_slots?.[0]?.date || '',
            '[[Time1]]': campaign.event_slots?.[0]?.time || '',
            '[[Date2]]': campaign.event_slots?.[1]?.date || '',
            '[[Time2]]': campaign.event_slots?.[1]?.time || '',
            '[[Date3]]': campaign.event_slots?.[2]?.date || '',
            '[[Time3]]': campaign.event_slots?.[2]?.time || '',
            '[[Calendly Link]]': campaign.calendly_link || '',
            '[[Calendly Link 1]]': campaign.event_slots?.[0]?.calendly_link || '',
            '[[Calendly Link 2]]': campaign.event_slots?.[1]?.calendly_link || '',
            '[[Calendly Link 3]]': campaign.event_slots?.[2]?.calendly_link || '',
        };
        
        // Apply all replacements
        for (const [key, value] of Object.entries(contactReplacements)) {
            const regex = new RegExp(key.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'g');
            mergedSubject = mergedSubject.replace(regex, value);
            mergedBody = mergedBody.replace(regex, value);
        }
        
        for (const [key, value] of Object.entries(campaignReplacements)) {
            const regex = new RegExp(key.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'g');
            mergedSubject = mergedSubject.replace(regex, value);
            mergedBody = mergedBody.replace(regex, value);
        }
        
        return { subject: mergedSubject, body: mergedBody };
    };

    const generateCommunications = async () => {
        if (!selectedContactType || selectedTemplates.size === 0) {
            alert('Please select contacts and at least one template');
            return;
        }

        setIsGenerating(true);
        setGenerationProgress(0);

        try {
            // Filter contacts based on selection
            const selectedContacts = selectedContactType === 'all' 
                ? contacts 
                : contacts.filter(c => c.is_rsvp);

            // Get selected template objects
            const templates = availableTemplates.filter(t => selectedTemplates.has(t.id));

            // Show warning for large datasets
            if (selectedContacts.length > 1000) {
                const proceed = window.confirm(
                    `You're about to generate communications for ${selectedContacts.length} contacts. ` +
                    `This may take a few moments. Continue?`
                );
                if (!proceed) {
                    setIsGenerating(false);
                    return;
                }
            }

            // Generate data with mail-merged templates in batches for better performance
            const batchSize = 100;
            const data: any[] = [];
            
            for (let i = 0; i < selectedContacts.length; i += batchSize) {
                const batch = selectedContacts.slice(i, i + batchSize);
                const batchData = batch.map(contact => {
                    const row: any = {
                        id: contact.id,
                        first_name: contact.first_name || '',
                        last_name: contact.last_name || '',
                        email: contact.email || '',
                        phone: contact.enriched_phone || contact.phone || '',
                        company: contact.enriched_company || contact.company || '',
                        title: contact.enriched_title || contact.title || '',
                        neighborhood: contact.neighborhood || '',
                    };

                    // Add mail-merged content for each selected template
                    templates.forEach(template => {
                        const merged = applyMailMerge(template, contact);
                        row[`${template.name}_subject`] = merged.subject;
                        row[`${template.name}_body`] = merged.body;
                    });

                    return row;
                });
                
                data.push(...batchData);
                
                // Update progress
                const progress = Math.round((i + batch.length) / selectedContacts.length * 100);
                setGenerationProgress(progress);
                
                // Allow UI to update
                await new Promise(resolve => setTimeout(resolve, 10));
            }

            // Create CSV content
            const headers = [
                'ID', 'First Name', 'Last Name', 'Email', 'Phone', 'Company', 'Title', 'Neighborhood',
                ...templates.flatMap(t => [`${t.name} Subject`, `${t.name} Body`])
            ];

            const csvContent = [
                headers.join(','),
                ...data.map(row => {
                    const values = [
                        row.id,
                        `"${row.first_name.replace(/"/g, '""')}"`,
                        `"${row.last_name.replace(/"/g, '""')}"`,
                        `"${row.email.replace(/"/g, '""')}"`,
                        `"${row.phone.replace(/"/g, '""')}"`,
                        `"${row.company.replace(/"/g, '""')}"`,
                        `"${row.title.replace(/"/g, '""')}"`,
                        `"${row.neighborhood.replace(/"/g, '""')}"`,
                        ...templates.flatMap(t => [
                            `"${(row[`${t.name}_subject`] || '').replace(/"/g, '""')}"`,
                            `"${(row[`${t.name}_body`] || '').replace(/"/g, '""').replace(/\n/g, ' ')}"`,
                        ])
                    ];
                    return values.join(',');
                })
            ].join('\n');

            // Save file metadata
            const fileId = `file_${Date.now()}`;
            const fileName = `${campaign.name}_${selectedContactType}_${new Date().toISOString().split('T')[0]}`;
            const file: GeneratedFile = {
                id: fileId,
                name: fileName,
                contactCount: selectedContacts.length,
                templateCount: templates.length,
                createdAt: new Date().toISOString(),
                googleSheetUrl: `https://docs.google.com/spreadsheets/d/${fileId}/edit` // Placeholder URL
            };

            // Save to localStorage (consider using IndexedDB for large files)
            if (csvContent.length < 5000000) { // Only store if less than 5MB
                localStorage.setItem(`file_${fileId}_data`, csvContent);
            }
            saveGeneratedFile(file);

            // Download CSV
            const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
            const link = document.createElement('a');
            const url = URL.createObjectURL(blob);
            link.setAttribute('href', url);
            link.setAttribute('download', `${fileName}.csv`);
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            URL.revokeObjectURL(url);

            alert(`Successfully generated communications for ${selectedContacts.length} contacts with ${templates.length} templates!`);
            
            // Reset selection
            setSelectedContactType(null);
            setSelectedTemplates(new Set());
            setGenerationProgress(0);

        } catch (error) {
            console.error('Error generating communications:', error);
            alert('Failed to generate communications. Please try again.');
        } finally {
            setIsGenerating(false);
            setGenerationProgress(0);
        }
    };

    const createGoogleSheet = async (file: GeneratedFile) => {
        // Get the CSV data from localStorage
        const csvData = localStorage.getItem(`file_${file.id}_data`);
        if (!csvData) {
            alert('File data not found');
            return;
        }

        // Parse CSV data
        const lines = csvData.split('\n');
        const headers = lines[0].split(',').map(h => h.replace(/"/g, ''));
        const rows = lines.slice(1).map(line => {
            // Parse CSV line (handling quoted fields)
            const regex = /("([^"]*)"|[^,]+|(?<=,)(?=,)|^(?=,)|(?<=,)$)/g;
            const matches = line.match(regex) || [];
            return matches.map(field => field.replace(/^"|"$/g, '').replace(/""/g, '"'));
        });

        // Create HTML table for easy copy-paste to Google Sheets
        const tableHTML = `
            <html>
            <head>
                <style>
                    table { border-collapse: collapse; width: 100%; }
                    th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                    th { background-color: #4CAF50; color: white; }
                    tr:nth-child(even) { background-color: #f2f2f2; }
                    .instructions { 
                        background: #e3f2fd; 
                        padding: 15px; 
                        margin: 20px 0; 
                        border-radius: 5px;
                        border-left: 4px solid #2196F3;
                    }
                </style>
            </head>
            <body>
                <div class="instructions">
                    <h2>Instructions to Import to Google Sheets:</h2>
                    <ol>
                        <li>Select all data below (Ctrl+A or Cmd+A)</li>
                        <li>Copy the selection (Ctrl+C or Cmd+C)</li>
                        <li>Open a new Google Sheet: <a href="https://sheets.new" target="_blank">sheets.new</a></li>
                        <li>Click on cell A1</li>
                        <li>Paste the data (Ctrl+V or Cmd+V)</li>
                    </ol>
                </div>
                <table>
                    <thead>
                        <tr>${headers.map(h => `<th>${h}</th>`).join('')}</tr>
                    </thead>
                    <tbody>
                        ${rows.map(row => `<tr>${row.map(cell => `<td>${cell}</td>`).join('')}</tr>`).join('')}
                    </tbody>
                </table>
            </body>
            </html>
        `;

        // Open in new window
        const newWindow = window.open('', '_blank');
        if (newWindow) {
            newWindow.document.write(tableHTML);
            newWindow.document.close();
        } else {
            alert('Please allow pop-ups to open the Google Sheets data');
        }
    };

    const deleteFile = (fileId: string) => {
        const updated = generatedFiles.filter(f => f.id !== fileId);
        setGeneratedFiles(updated);
        localStorage.setItem(`campaign_${campaignId}_files`, JSON.stringify(updated));
        localStorage.removeItem(`file_${fileId}_data`);
    };

    return (
        <Card>
            <Flex direction="column" gap="4">
                <Box>
                    <Heading size="4" mb="2">Create Communications</Heading>
                    <Text size="2" color="gray">
                        Generate mail-merged communications for your contacts
                    </Text>
                </Box>

                {/* Step 1: Select Contacts */}
                <Box>
                    <Text size="3" weight="bold" mb="3">
                        Step 1: Select Contacts
                    </Text>
                    <Flex gap="3">
                        <Button
                            size="3"
                            variant={selectedContactType === 'all' ? 'solid' : 'soft'}
                            onClick={() => selectContactType('all')}
                        >
                            <PersonIcon />
                            Select All Contacts ({contacts.length})
                        </Button>
                        <Button
                            size="3"
                            variant={selectedContactType === 'rsvp' ? 'solid' : 'soft'}
                            onClick={() => selectContactType('rsvp')}
                        >
                            <CheckCircledIcon />
                            Select RSVPs ({contacts.filter(c => c.is_rsvp).length})
                        </Button>
                    </Flex>
                </Box>

                {/* Step 2: Select Templates */}
                {selectedContactType && (
                    <Box>
                        <Text size="3" weight="bold" mb="3">
                            Step 2: Select Email Templates
                        </Text>
                        {availableTemplates.length === 0 ? (
                            <Callout.Root color="amber">
                                <Callout.Icon>
                                    <InfoCircledIcon />
                                </Callout.Icon>
                                <Callout.Text>
                                    No email templates available. Please create templates first.
                                </Callout.Text>
                            </Callout.Root>
                        ) : (
                            <ScrollArea style={{ maxHeight: '300px' }}>
                                <Flex direction="column" gap="2">
                                    {availableTemplates.map(template => (
                                        <Card key={template.id} style={{ padding: '12px' }}>
                                            <Flex align="center" gap="3">
                                                <Checkbox
                                                    checked={selectedTemplates.has(template.id)}
                                                    onCheckedChange={() => toggleTemplate(template.id)}
                                                />
                                                <Box style={{ flex: 1 }}>
                                                    <Text weight="medium">{template.name}</Text>
                                                </Box>
                                                <IconButton
                                                    size="1"
                                                    variant="ghost"
                                                    onClick={() => handleEditTemplate(template)}
                                                >
                                                    <Pencil1Icon />
                                                </IconButton>
                                                {template.template_type && (
                                                    <Badge>{template.template_type}</Badge>
                                                )}
                                            </Flex>
                                        </Card>
                                    ))}
                                </Flex>
                            </ScrollArea>
                        )}
                        
                        {selectedTemplates.size > 0 && (
                            <Text size="2" color="blue" mt="2">
                                {selectedTemplates.size} template(s) selected
                            </Text>
                        )}
                    </Box>
                )}

                {/* Step 3: Generate */}
                {selectedContactType && selectedTemplates.size > 0 && (
                    <Box>
                        <Callout.Root color="blue" mb="3">
                            <Callout.Icon>
                                <InfoCircledIcon />
                            </Callout.Icon>
                            <Callout.Text>
                                This will generate a CSV file with {
                                    selectedContactType === 'all' ? contacts.length : contacts.filter(c => c.is_rsvp).length
                                } contacts and {selectedTemplates.size} email template(s). 
                                Each template will be mail-merged and added as separate columns.
                            </Callout.Text>
                        </Callout.Root>
                        
                        <Button
                            size="3"
                            onClick={generateCommunications}
                            disabled={isGenerating}
                        >
                            {isGenerating ? `Generating... ${generationProgress}%` : 'Generate Communications'}
                        </Button>
                    </Box>
                )}

                {/* Generated Files */}
                {generatedFiles.length > 0 && (
                    <Box>
                        <Text size="3" weight="bold" mb="3">
                            Generated Files
                        </Text>
                        <Flex direction="column" gap="2">
                            {generatedFiles.map(file => (
                                <Card key={file.id}>
                                    <Flex align="center" justify="between">
                                        <Box>
                                            <Text weight="medium">{file.name}</Text>
                                            <Text size="1" color="gray">
                                                {file.contactCount} contacts · {file.templateCount} templates · {
                                                    new Date(file.createdAt).toLocaleDateString()
                                                }
                                            </Text>
                                        </Box>
                                        <Flex gap="2">
                                            <Button
                                                variant="soft"
                                                size="2"
                                                color="green"
                                                onClick={() => createGoogleSheet(file)}
                                            >
                                                <ExternalLinkIcon />
                                                Create Google Sheet
                                            </Button>
                                            <IconButton
                                                variant="soft"
                                                color="red"
                                                size="2"
                                                onClick={() => deleteFile(file.id)}
                                            >
                                                <Cross2Icon />
                                            </IconButton>
                                        </Flex>
                                    </Flex>
                                </Card>
                            ))}
                        </Flex>
                    </Box>
                )}
            </Flex>

            {/* Edit Template Modal */}
            <Dialog.Root open={showEditModal} onOpenChange={setShowEditModal}>
                <Dialog.Content style={{ maxWidth: 600 }}>
                    <Dialog.Title>Edit Email Template</Dialog.Title>
                    <Dialog.Description>
                        Update the template content below
                    </Dialog.Description>
                    
                    <Flex direction="column" gap="4" mt="4">
                        <Box>
                            <Text as="label" size="2" mb="1" weight="medium">
                                Template Name
                            </Text>
                            <TextField.Root
                                value={templateForm.name}
                                onChange={(e) => setTemplateForm({ ...templateForm, name: e.target.value })}
                            />
                        </Box>
                        
                        <Box>
                            <Text as="label" size="2" mb="1" weight="medium">
                                Subject Line
                            </Text>
                            <TextField.Root
                                value={templateForm.subject}
                                onChange={(e) => setTemplateForm({ ...templateForm, subject: e.target.value })}
                            />
                        </Box>
                        
                        <Box>
                            <Text as="label" size="2" mb="1" weight="medium">
                                Email Body
                            </Text>
                            <TextArea
                                value={templateForm.body}
                                onChange={(e) => setTemplateForm({ ...templateForm, body: e.target.value })}
                                rows={15}
                                style={{ fontFamily: 'monospace', fontSize: '12px' }}
                            />
                            <Text size="1" color="gray" mt="1">
                                Use {'{{FirstName}}'}, {'{{Company}}'}, [[City]], [[State]], etc. for mail merge
                            </Text>
                        </Box>
                        
                        <Flex gap="3" justify="end">
                            <Dialog.Close>
                                <Button variant="soft">Cancel</Button>
                            </Dialog.Close>
                            <Button onClick={handleUpdateTemplate}>
                                Update Template
                            </Button>
                        </Flex>
                    </Flex>
                </Dialog.Content>
            </Dialog.Root>
        </Card>
    );
}; 