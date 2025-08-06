import React, { useState, useEffect } from 'react';
import { 
    Box, Flex, Text, Card, Button, Badge, ScrollArea, 
    Checkbox, TextField, TextArea, Callout, IconButton, Dialog,
    Separator, Tabs, Heading
} from '@radix-ui/themes';
import { 
    InfoCircledIcon, ExternalLinkIcon, Cross2Icon, Pencil1Icon,
    FileIcon, ImageIcon, UploadIcon, PersonIcon, CheckCircledIcon, DownloadIcon
} from '@radix-ui/react-icons';
import api from '../api';

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
    
    // Image upload states
    const [uploadedImages, setUploadedImages] = useState<{url: string, name: string}[]>([]);
    const [isUploadingImage, setIsUploadingImage] = useState(false);
    const imageInputRef = React.useRef<HTMLInputElement>(null);

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
            await api.put(`/api/email-templates/${editingTemplate.id}`, templateForm);
            await fetchTemplates();
            setShowEditModal(false);
            setEditingTemplate(null);
            alert('Template updated successfully');
        } catch (err) {
            console.error('Failed to update template:', err);
            alert('Failed to update template');
        }
    };

    const handleImageUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
        const file = event.target.files?.[0];
        if (!file) return;

        setIsUploadingImage(true);
        
        try {
            // For now, we'll use a data URL for the image
            // In production, you'd upload to a server or cloud storage
            const reader = new FileReader();
            reader.onloadend = () => {
                const imageUrl = reader.result as string;
                const newImage = { url: imageUrl, name: file.name };
                setUploadedImages(prev => [...prev, newImage]);
                
                // Insert image reference at cursor position in the template body
                const imageTag = `<img src="${imageUrl}" alt="${file.name}" style="max-width: 100%; height: auto;" />`;
                setTemplateForm(prev => ({
                    ...prev,
                    body: prev.body + '\n' + imageTag + '\n'
                }));
                
                setIsUploadingImage(false);
            };
            reader.readAsDataURL(file);
        } catch (error) {
            console.error('Error uploading image:', error);
            alert('Failed to upload image');
            setIsUploadingImage(false);
        }
    };

    const insertImageReference = (imageUrl: string, imageName: string) => {
        const imageTag = `<img src="${imageUrl}" alt="${imageName}" style="max-width: 100%; height: auto;" />`;
        setTemplateForm(prev => ({
            ...prev,
            body: prev.body + '\n' + imageTag + '\n'
        }));
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
                            `"${(row[`${t.name}_body`] || '').replace(/"/g, '""')}"`,
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

            // Don't download CSV automatically - user will click "Create Google Sheet" button
            // const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
            // const link = document.createElement('a');
            // const url = URL.createObjectURL(blob);
            // link.setAttribute('href', url);
            // link.setAttribute('download', `${fileName}.csv`);
            // document.body.appendChild(link);
            // link.click();
            // document.body.removeChild(link);
            // URL.revokeObjectURL(url);

            alert(`Successfully generated communications for ${selectedContacts.length} contacts with ${templates.length} templates! Click "Create Google Sheet" to open the data.`);
            
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
            alert('File data not found. Please regenerate the file.');
            return;
        }

        // Parse CSV data
        const lines = csvData.split('\n');
        const headers = lines[0].split(',').map(h => h.replace(/"/g, ''));
        const rows = lines.slice(1).map(line => {
            // Parse CSV line (handling quoted fields)
            const regex = /("([^"]*)"|[^,]+|(?<=,)(?=,)|^(?=,)|(?<=,)$)/g;
            const matches = line.match(regex) || [];
            return matches.map(field => {
                // Remove quotes and unescape double quotes
                let cleanField = field.replace(/^"|"$/g, '').replace(/""/g, '"');
                // Convert newlines to HTML breaks for display
                cleanField = cleanField.replace(/\n/g, '<br>');
                // Ensure images are properly formatted
                cleanField = cleanField.replace(/<img/g, '<img style="max-width: 200px; height: auto;"');
                return cleanField;
            });
        });

        // Create HTML table for easy copy-paste to Google Sheets
        const tableHTML = `
            <!DOCTYPE html>
            <html>
            <head>
                <title>${file.name} - Google Sheets Export</title>
                <meta charset="UTF-8">
                <style>
                    body { font-family: Arial, sans-serif; margin: 20px; }
                    table { border-collapse: collapse; width: 100%; margin-top: 20px; }
                    th, td { 
                        border: 1px solid #ddd; 
                        padding: 8px; 
                        text-align: left; 
                        vertical-align: top;
                        white-space: pre-wrap;
                        word-wrap: break-word;
                    }
                    th { background-color: #4CAF50; color: white; position: sticky; top: 0; }
                    tr:nth-child(even) { background-color: #f2f2f2; }
                    td img { max-width: 200px; height: auto; display: block; margin: 5px 0; }
                    .instructions { 
                        background: #e3f2fd; 
                        padding: 20px; 
                        margin: 20px 0; 
                        border-radius: 8px;
                        border-left: 4px solid #2196F3;
                    }
                    .instructions h2 { margin-top: 0; color: #1976D2; }
                    .instructions ol { margin: 10px 0; padding-left: 25px; }
                    .instructions li { margin: 8px 0; }
                    .instructions a { 
                        color: #1976D2; 
                        text-decoration: none; 
                        font-weight: bold;
                        background: #fff;
                        padding: 4px 8px;
                        border-radius: 4px;
                        border: 1px solid #1976D2;
                    }
                    .instructions a:hover { background: #1976D2; color: white; }
                    .copy-button {
                        background: #4CAF50;
                        color: white;
                        border: none;
                        padding: 10px 20px;
                        border-radius: 5px;
                        cursor: pointer;
                        font-size: 16px;
                        margin: 10px 0;
                    }
                    .copy-button:hover { background: #45a049; }
                    .format-note {
                        background: #fff3cd;
                        border: 1px solid #ffc107;
                        padding: 10px;
                        margin: 10px 0;
                        border-radius: 5px;
                        color: #856404;
                    }
                </style>
                <script>
                    function selectAllData() {
                        const range = document.createRange();
                        range.selectNode(document.getElementById('dataTable'));
                        window.getSelection().removeAllRanges();
                        window.getSelection().addRange(range);
                        try {
                            document.execCommand('copy');
                            alert('Data copied to clipboard! Now paste it into Google Sheets.');
                        } catch (err) {
                            alert('Please manually select and copy the table.');
                        }
                    }
                </script>
            </head>
            <body>
                <div class="instructions">
                    <h2>Export to Google Sheets</h2>
                    <button class="copy-button" onclick="selectAllData()">📋 Copy All Data</button>
                    <ol>
                        <li>Click the "Copy All Data" button above, or select all data manually (Ctrl+A or Cmd+A)</li>
                        <li>Open Google Sheets: <a href="https://sheets.new" target="_blank">Create New Sheet →</a></li>
                        <li>Click on cell A1 in the new sheet</li>
                        <li>Paste the data (Ctrl+V or Cmd+V)</li>
                        <li>The data will automatically format into columns</li>
                    </ol>
                    <div class="format-note">
                        <strong>Note:</strong> Line breaks and formatting are preserved. Images will be displayed as HTML tags.
                        For best results in Google Sheets, you may need to adjust row heights after pasting.
                    </div>
                </div>
                <table id="dataTable">
                    <thead>
                        <tr>${headers.map(h => `<th>${h}</th>`).join('')}</tr>
                    </thead>
                    <tbody>
                        ${rows.map(row => `<tr>${row.map(cell => `<td>${cell || ''}</td>`).join('')}</tr>`).join('')}
                    </tbody>
                </table>
            </body>
            </html>
        `;

        // Try to open in new window/tab
        const newWindow = window.open('', '_blank');
        if (newWindow) {
            newWindow.document.write(tableHTML);
            newWindow.document.close();
            newWindow.document.title = `${file.name} - Google Sheets Export`;
        } else {
            // Fallback: Create a blob and open it
            const blob = new Blob([tableHTML], { type: 'text/html' });
            const url = URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.target = '_blank';
            link.click();
            
            // Clean up
            setTimeout(() => URL.revokeObjectURL(url), 100);
            
            // Alert user about popup blocker
            alert('A popup blocker may have prevented opening the data. The file has been opened in a new tab. If it doesn\'t appear, please check your popup blocker settings.');
        }
    };

    const deleteFile = (fileId: string) => {
        const updatedFiles = generatedFiles.filter(f => f.id !== fileId);
        setGeneratedFiles(updatedFiles);
        localStorage.setItem(`campaign_${campaignId}_files`, JSON.stringify(updatedFiles));
        localStorage.removeItem(`file_${fileId}_data`);
    };

    const downloadCSV = (file: GeneratedFile) => {
        // Get the CSV data from localStorage
        const csvData = localStorage.getItem(`file_${file.id}_data`);
        if (!csvData) {
            alert('File data not found. Please regenerate the file.');
            return;
        }

        // Create and download CSV
        const blob = new Blob([csvData], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        const url = URL.createObjectURL(blob);
        link.setAttribute('href', url);
        link.setAttribute('download', `${file.name}.csv`);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
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
                                            <Button
                                                variant="soft"
                                                size="2"
                                                color="blue"
                                                onClick={() => downloadCSV(file)}
                                            >
                                                <DownloadIcon />
                                                Download CSV
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
                <Dialog.Content style={{ maxWidth: 700, maxHeight: '90vh', overflowY: 'auto' }}>
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
                        
                        {/* Image Upload Section */}
                        <Box>
                            <Text as="label" size="2" mb="1" weight="medium">
                                Images
                            </Text>
                            <Card style={{ padding: '12px', backgroundColor: 'var(--gray-1)' }}>
                                <input
                                    ref={imageInputRef}
                                    type="file"
                                    accept="image/*"
                                    onChange={handleImageUpload}
                                    style={{ display: 'none' }}
                                />
                                <Button
                                    variant="soft"
                                    size="2"
                                    onClick={() => imageInputRef.current?.click()}
                                    disabled={isUploadingImage}
                                >
                                    <UploadIcon />
                                    {isUploadingImage ? 'Uploading...' : 'Upload Image'}
                                </Button>
                                
                                {uploadedImages.length > 0 && (
                                    <Box mt="3">
                                        <Text size="1" weight="medium" mb="2">Uploaded Images (click to insert):</Text>
                                        <Flex gap="2" wrap="wrap">
                                            {uploadedImages.map((img, index) => (
                                                <Card 
                                                    key={index}
                                                    style={{ 
                                                        padding: '4px', 
                                                        cursor: 'pointer',
                                                        border: '1px solid var(--gray-5)'
                                                    }}
                                                    onClick={() => insertImageReference(img.url, img.name)}
                                                >
                                                    <Flex direction="column" align="center" gap="1">
                                                        <img 
                                                            src={img.url} 
                                                            alt={img.name}
                                                            style={{ 
                                                                width: '80px', 
                                                                height: '80px', 
                                                                objectFit: 'cover',
                                                                borderRadius: '4px'
                                                            }}
                                                        />
                                                        <Text size="1" style={{ 
                                                            maxWidth: '80px', 
                                                            overflow: 'hidden', 
                                                            textOverflow: 'ellipsis',
                                                            whiteSpace: 'nowrap'
                                                        }}>
                                                            {img.name}
                                                        </Text>
                                                    </Flex>
                                                </Card>
                                            ))}
                                        </Flex>
                                    </Box>
                                )}
                                
                                <Text size="1" color="gray" mt="2">
                                    Images will be embedded in the email template. Click on an uploaded image to insert it at the current cursor position.
                                </Text>
                            </Card>
                        </Box>
                        
                        <Box>
                            <Text as="label" size="2" mb="1" weight="medium">
                                Email Body
                            </Text>
                            <TextArea
                                value={templateForm.body}
                                onChange={(e) => setTemplateForm({ ...templateForm, body: e.target.value })}
                                rows={15}
                                style={{ 
                                    fontFamily: 'monospace', 
                                    fontSize: '12px',
                                    whiteSpace: 'pre-wrap'
                                }}
                            />
                            <Text size="1" color="gray" mt="1">
                                Use {'{{FirstName}}'}, {'{{Company}}'}, [[City]], [[State]], etc. for mail merge.
                                Line breaks and formatting will be preserved.
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