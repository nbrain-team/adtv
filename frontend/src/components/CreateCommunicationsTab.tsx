import React, { useState, useEffect } from 'react';
import { 
    Box, Flex, Text, Card, Button, Badge, ScrollArea, 
    Checkbox, TextField, TextArea, Callout, IconButton, Dialog,
    Separator, Tabs, Heading
} from '@radix-ui/themes';
import { 
    InfoCircledIcon, ExternalLinkIcon, Cross2Icon, Pencil1Icon,
    FileIcon, ImageIcon, UploadIcon, PersonIcon, CheckCircledIcon, DownloadIcon,
    PlusIcon, TrashIcon, EyeOpenIcon
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
    
    // Template Manager states
    const [showTemplateManager, setShowTemplateManager] = useState(false);
    const [showCreateTemplate, setShowCreateTemplate] = useState(false);
    const [newTemplateForm, setNewTemplateForm] = useState({
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
            // Add timestamp to prevent caching issues
            const response = await api.get(`/api/campaigns/${campaignId}/email-templates?t=${Date.now()}`);
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
        
        // Extract existing images from the template body
        const imageRegex = /<img[^>]+src="([^"]+)"[^>]*>/g;
        const existingImages: {url: string, name: string}[] = [];
        let match;
        
        while ((match = imageRegex.exec(template.body)) !== null) {
            const url = match[1];
            // Extract filename from URL if possible
            const filename = url.split('/').pop() || 'image';
            existingImages.push({ url, name: filename });
        }
        
        setUploadedImages(existingImages);
        setShowEditModal(true);
    };

    const handleUpdateTemplate = async () => {
        if (!editingTemplate) return;
        
        try {
            // Map frontend fields to backend expected fields
            const updateData = {
                name: templateForm.name,
                subject: templateForm.subject,  // Campaign templates use 'subject'
                body: templateForm.body,         // Campaign templates use 'body'
                template_type: templateForm.template_type
            };
            
            const response = await api.put(`/api/campaigns/${campaignId}/email-templates/${editingTemplate.id}`, updateData);
            
            // Log the response to debug
            console.log('Template update response:', response.data);
            
            // Immediately update the local state with the new template data
            setAvailableTemplates(prev => prev.map(t => 
                t.id === editingTemplate.id 
                    ? { ...t, ...templateForm }
                    : t
            ));
            
            // Close modal first
            setShowEditModal(false);
            setEditingTemplate(null);
            setUploadedImages([]); // Clear uploaded images after save
            
            // Wait a moment for backend to fully commit
            await new Promise(resolve => setTimeout(resolve, 500));
            
            // Then fetch fresh data from server to ensure sync
            await fetchTemplates();
            
            alert('Template updated successfully');
        } catch (err: any) {
            console.error('Failed to update template:', err);
            const errorMessage = err.response?.data?.detail || err.message || 'Failed to update template';
            alert(`Error updating template: ${errorMessage}`);
        }
    };

    const handleCreateTemplate = async () => {
        try {
            const createData = {
                name: newTemplateForm.name,
                subject: newTemplateForm.subject,
                body: newTemplateForm.body,
                template_type: newTemplateForm.template_type
            };
            
            await api.post(`/api/campaigns/${campaignId}/email-templates`, createData);
            
            // Reset form
            setNewTemplateForm({
                name: '',
                subject: '',
                body: '',
                template_type: 'general'
            });
            
            setShowCreateTemplate(false);
            
            // Refresh templates list
            await fetchTemplates();
            
            alert('Template created successfully');
        } catch (err: any) {
            console.error('Failed to create template:', err);
            const errorMessage = err.response?.data?.detail || err.message || 'Failed to create template';
            alert(`Error creating template: ${errorMessage}`);
        }
    };

    const handleDeleteTemplate = async (templateId: string, templateName: string) => {
        if (!confirm(`Are you sure you want to delete the template "${templateName}"?`)) {
            return;
        }
        
        try {
            await api.delete(`/api/campaigns/${campaignId}/email-templates/${templateId}`);
            
            // Refresh templates list
            await fetchTemplates();
            
            alert('Template deleted successfully');
        } catch (err: any) {
            console.error('Failed to delete template:', err);
            const errorMessage = err.response?.data?.detail || err.message || 'Failed to delete template';
            alert(`Error deleting template: ${errorMessage}`);
        }
    };

    const handleImageUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
        const file = event.target.files?.[0];
        if (!file) return;

        setIsUploadingImage(true);
        
        try {
            // Upload image to server instead of using base64
            const formData = new FormData();
            formData.append('file', file);
            
            // Upload to the backend endpoint
            const response = await api.post(`/api/campaigns/${campaignId}/upload-image`, formData, {
                headers: {
                    'Content-Type': 'multipart/form-data',
                }
            });
            
            // Server returns a URL instead of base64
            const imageData = response.data;
            const newImage = { 
                url: imageData.url, 
                name: file.name 
            };
            
            setUploadedImages(prev => [...prev, newImage]);
            setIsUploadingImage(false);
            
            alert(`Image "${file.name}" uploaded! Click on the image below to copy its HTML code.`);
        } catch (error) {
            console.error('Error uploading image:', error);
            alert('Failed to upload image. Please try again.');
            setIsUploadingImage(false);
        }
    };

    const copyImageHTML = (imageUrl: string, imageName: string) => {
        // Create a properly formatted image tag with the server URL
        const fullUrl = imageUrl.startsWith('http') ? imageUrl : `${window.location.origin}${imageUrl}`;
        const imageTag = `<img src="${fullUrl}" alt="${imageName}" style="max-width: 100%; height: auto;" />`;
        
        // Copy to clipboard
        navigator.clipboard.writeText(imageTag).then(() => {
            alert(`Image HTML copied to clipboard! Now paste it in the email body where you want the image to appear.`);
        }).catch(err => {
            // Fallback for older browsers
            const textArea = document.createElement('textarea');
            textArea.value = imageTag;
            document.body.appendChild(textArea);
            textArea.select();
            document.execCommand('copy');
            document.body.removeChild(textArea);
            alert(`Image HTML copied! Paste it in the email body where you want the image.`);
        });
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
                    // Helper function to escape CSV values and preserve formatting
                    const escapeCSV = (value: string) => {
                        // Keep newlines but ensure they're properly quoted
                        // Escape double quotes
                        const escaped = value.replace(/"/g, '""');
                        // Always quote fields that contain newlines, commas, or quotes
                        return `"${escaped}"`;
                    };
                    
                    const values = [
                        row.id,
                        escapeCSV(row.first_name),
                        escapeCSV(row.last_name),
                        escapeCSV(row.email),
                        escapeCSV(row.phone),
                        escapeCSV(row.company),
                        escapeCSV(row.title),
                        escapeCSV(row.neighborhood),
                        ...templates.flatMap(t => [
                            escapeCSV(row[`${t.name}_subject`] || ''),
                            escapeCSV(row[`${t.name}_body`] || ''),
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

        // Parse CSV data with proper handling of quoted fields containing newlines
        const parseCSV = (text: string) => {
            const rows: string[][] = [];
            let currentRow: string[] = [];
            let currentField = '';
            let inQuotes = false;
            
            for (let i = 0; i < text.length; i++) {
                const char = text[i];
                const nextChar = text[i + 1];
                
                if (inQuotes) {
                    if (char === '"' && nextChar === '"') {
                        // Escaped quote
                        currentField += '"';
                        i++; // Skip next quote
                    } else if (char === '"') {
                        // End of quoted field
                        inQuotes = false;
                    } else {
                        // Regular character in quoted field (including newlines)
                        currentField += char;
                    }
                } else {
                    if (char === '"') {
                        // Start of quoted field
                        inQuotes = true;
                    } else if (char === ',') {
                        // End of field
                        currentRow.push(currentField);
                        currentField = '';
                    } else if (char === '\n' || (char === '\r' && nextChar === '\n')) {
                        // End of row
                        currentRow.push(currentField);
                        if (currentRow.length > 0 || rows.length > 0) {
                            rows.push(currentRow);
                        }
                        currentRow = [];
                        currentField = '';
                        if (char === '\r' && nextChar === '\n') {
                            i++; // Skip \n in \r\n
                        }
                    } else if (char !== '\r') {
                        // Regular character
                        currentField += char;
                    }
                }
            }
            
            // Add last field and row if needed
            if (currentField || currentRow.length > 0) {
                currentRow.push(currentField);
            }
            if (currentRow.length > 0) {
                rows.push(currentRow);
            }
            
            return rows;
        };
        
        const parsedData = parseCSV(csvData);
        const headers = parsedData[0] || [];
        const rows = parsedData.slice(1).map(row => {
            return row.map(field => {
                // Convert newlines to HTML breaks for display
                let cleanField = field.replace(/\n/g, '<br>');
                cleanField = cleanField.replace(/\r/g, '');
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
                    table { border-collapse: collapse; width: 100%; margin-top: 20px; table-layout: fixed; }
                    th, td { 
                        border: 1px solid #ddd; 
                        padding: 8px; 
                        text-align: left; 
                        vertical-align: top;
                        white-space: pre-wrap;
                        word-wrap: break-word;
                        max-width: 500px;
                        overflow: hidden;
                    }
                    th { background-color: #4CAF50; color: white; position: sticky; top: 0; z-index: 10; }
                    tr:nth-child(even) { background-color: #f2f2f2; }
                    td img { max-width: 200px; height: auto; display: block; margin: 5px 0; }
                    .email-cell { 
                        max-height: 300px; 
                        overflow-y: auto; 
                        font-size: 12px;
                        line-height: 1.4;
                    }
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
                        <strong>Note:</strong> Email templates are contained in single cells with line breaks preserved.
                        For best results in Google Sheets, you may need to adjust row heights after pasting.
                    </div>
                </div>
                <table id="dataTable">
                    <thead>
                        <tr>${headers.map(h => `<th>${h}</th>`).join('')}</tr>
                    </thead>
                    <tbody>
                        ${rows.map(row => {
                            return `<tr>${row.map((cell, index) => {
                                // Check if this is an email body column (contains template content)
                                const isEmailContent = headers[index]?.toLowerCase().includes('body');
                                const cellClass = isEmailContent ? 'email-cell' : '';
                                return `<td class="${cellClass}">${cell || ''}</td>`;
                            }).join('')}</tr>`;
                        }).join('')}
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
                <Flex justify="between" align="center">
                    <Box>
                        <Heading size="4" mb="2">Create Communications</Heading>
                        <Text size="2" color="gray">
                            Generate mail-merged communications for your contacts
                        </Text>
                    </Box>
                    <Button
                        variant="soft"
                        size="2"
                        onClick={() => setShowTemplateManager(true)}
                    >
                        <EyeOpenIcon />
                        View & Edit Email Templates
                    </Button>
                </Flex>

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

            {/* Template Manager Modal */}
            <Dialog.Root open={showTemplateManager} onOpenChange={setShowTemplateManager}>
                <Dialog.Content style={{ maxWidth: 900, maxHeight: '90vh', overflowY: 'auto' }}>
                    <Dialog.Title>Email Templates Manager</Dialog.Title>
                    <Dialog.Description>
                        Create, edit, and manage your email templates
                    </Dialog.Description>
                    
                    <Flex direction="column" gap="4" mt="4">
                        <Flex justify="between" align="center">
                            <Text size="3" weight="bold">
                                Available Templates ({availableTemplates.length})
                            </Text>
                            <Button
                                size="2"
                                onClick={() => setShowCreateTemplate(true)}
                            >
                                <PlusIcon />
                                Create New Template
                            </Button>
                        </Flex>
                        
                        {showCreateTemplate && (
                            <Card style={{ padding: '16px', backgroundColor: 'var(--gray-1)' }}>
                                <Flex direction="column" gap="3">
                                    <Text weight="bold">New Template</Text>
                                    
                                    <Box>
                                        <Text as="label" size="2" mb="1" weight="medium">
                                            Template Name
                                        </Text>
                                        <TextField.Root
                                            placeholder="e.g., Follow-up Email"
                                            value={newTemplateForm.name}
                                            onChange={(e) => setNewTemplateForm({ ...newTemplateForm, name: e.target.value })}
                                        />
                                    </Box>
                                    
                                    <Box>
                                        <Text as="label" size="2" mb="1" weight="medium">
                                            Subject Line
                                        </Text>
                                        <TextField.Root
                                            placeholder="e.g., Hey {{FirstName}}, following up..."
                                            value={newTemplateForm.subject}
                                            onChange={(e) => setNewTemplateForm({ ...newTemplateForm, subject: e.target.value })}
                                        />
                                    </Box>
                                    
                                    <Box>
                                        <Text as="label" size="2" mb="1" weight="medium">
                                            Email Body
                                        </Text>
                                        <TextArea
                                            placeholder="Enter your email template here..."
                                            value={newTemplateForm.body}
                                            onChange={(e) => setNewTemplateForm({ ...newTemplateForm, body: e.target.value })}
                                            rows={8}
                                            style={{ fontFamily: 'monospace', fontSize: '12px' }}
                                        />
                                        <Text size="1" color="gray" mt="1">
                                            Use {'{{FirstName}}'}, {'{{Company}}'}, [[City]], [[State]], etc. for mail merge
                                        </Text>
                                    </Box>
                                    
                                    <Flex gap="2" justify="end">
                                        <Button
                                            variant="soft"
                                            onClick={() => {
                                                setShowCreateTemplate(false);
                                                setNewTemplateForm({
                                                    name: '',
                                                    subject: '',
                                                    body: '',
                                                    template_type: 'general'
                                                });
                                            }}
                                        >
                                            Cancel
                                        </Button>
                                        <Button
                                            onClick={handleCreateTemplate}
                                            disabled={!newTemplateForm.name || !newTemplateForm.subject || !newTemplateForm.body}
                                        >
                                            Create Template
                                        </Button>
                                    </Flex>
                                </Flex>
                            </Card>
                        )}
                        
                        <ScrollArea style={{ maxHeight: '400px' }}>
                            <Flex direction="column" gap="2">
                                {availableTemplates.length === 0 ? (
                                    <Card style={{ padding: '20px', textAlign: 'center' }}>
                                        <Text color="gray">No templates yet. Create your first template!</Text>
                                    </Card>
                                ) : (
                                    availableTemplates.map(template => (
                                        <Card key={template.id} style={{ padding: '12px' }}>
                                            <Flex justify="between" align="start">
                                                <Box style={{ flex: 1 }}>
                                                    <Flex align="center" gap="2" mb="1">
                                                        <Text weight="bold" size="3">{template.name}</Text>
                                                        {template.template_type && (
                                                            <Badge size="1">{template.template_type}</Badge>
                                                        )}
                                                    </Flex>
                                                    <Text size="2" color="gray" style={{ display: 'block', marginBottom: '4px' }}>
                                                        Subject: {template.subject.substring(0, 80)}
                                                        {template.subject.length > 80 ? '...' : ''}
                                                    </Text>
                                                    <Text size="1" color="gray">
                                                        Body preview: {template.body.substring(0, 100)}
                                                        {template.body.length > 100 ? '...' : ''}
                                                    </Text>
                                                </Box>
                                                <Flex gap="2">
                                                    <IconButton
                                                        size="2"
                                                        variant="soft"
                                                        onClick={() => {
                                                            handleEditTemplate(template);
                                                            setShowTemplateManager(false);
                                                        }}
                                                    >
                                                        <Pencil1Icon />
                                                    </IconButton>
                                                    <IconButton
                                                        size="2"
                                                        variant="soft"
                                                        color="red"
                                                        onClick={() => handleDeleteTemplate(template.id, template.name)}
                                                    >
                                                        <TrashIcon />
                                                    </IconButton>
                                                </Flex>
                                            </Flex>
                                        </Card>
                                    ))
                                )}
                            </Flex>
                        </ScrollArea>
                        
                        <Flex justify="end">
                            <Dialog.Close>
                                <Button variant="soft">Close</Button>
                            </Dialog.Close>
                        </Flex>
                    </Flex>
                </Dialog.Content>
            </Dialog.Root>

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
                                        <Text size="1" weight="medium" mb="2">Click an image to copy its HTML code:</Text>
                                        <Flex gap="2" wrap="wrap">
                                            {uploadedImages.map((img, index) => (
                                                <Card 
                                                    key={index}
                                                    style={{ 
                                                        padding: '4px', 
                                                        cursor: 'pointer',
                                                        border: '1px solid var(--gray-5)',
                                                        position: 'relative'
                                                    }}
                                                    onClick={() => copyImageHTML(img.url, img.name)}
                                                >
                                                    <Flex direction="column" align="center" gap="1">
                                                        <img 
                                                            src={img.url.startsWith('http') || img.url.startsWith('data:') 
                                                                ? img.url 
                                                                : `${window.location.origin}${img.url}`} 
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
                                                        <Badge size="1" color="blue">Click to copy</Badge>
                                                    </Flex>
                                                </Card>
                                            ))}
                                        </Flex>
                                    </Box>
                                )}
                                
                                <Card style={{ padding: '8px', backgroundColor: 'var(--blue-1)', marginTop: '8px' }}>
                                    <Text size="1" color="blue">
                                        <strong>How to use images:</strong><br/>
                                        1. Upload an image using the button above<br/>
                                        2. Click on the uploaded image thumbnail to copy its HTML code<br/>
                                        3. Paste the code (Ctrl+V or Cmd+V) anywhere in the email body<br/>
                                        4. The image will appear in that location when the email is sent
                                    </Text>
                                </Card>
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
                            <Flex direction="column" gap="1" mt="1">
                                <Text size="1" color="gray">
                                    Use {'{{FirstName}}'}, {'{{Company}}'}, [[City]], [[State]], etc. for mail merge.
                                </Text>
                                <Text size="1" color="gray">
                                    For hyperlinks: {'<a href="[[VIDEO-LINK]]">Click here to watch</a>'}
                                </Text>
                                <Text size="1" color="gray">
                                    Line breaks and formatting will be preserved.
                                </Text>
                            </Flex>
                            
                            {/* Quick Insert Buttons */}
                            <Flex gap="2" mt="2" wrap="wrap">
                                <Text size="1" weight="medium">Quick Insert:</Text>
                                <Button
                                    size="1"
                                    variant="soft"
                                    type="button"
                                    onClick={() => {
                                        const linkHtml = '<a href="[[VIDEO-LINK]]">Watch our video</a>';
                                        setTemplateForm({ 
                                            ...templateForm, 
                                            body: templateForm.body + '\n' + linkHtml 
                                        });
                                    }}
                                >
                                    + Video Link
                                </Button>
                                <Button
                                    size="1"
                                    variant="soft"
                                    type="button"
                                    onClick={() => {
                                        const linkHtml = '<a href="[[Event-Link]]">Event details</a>';
                                        setTemplateForm({ 
                                            ...templateForm, 
                                            body: templateForm.body + '\n' + linkHtml 
                                        });
                                    }}
                                >
                                    + Event Link
                                </Button>
                                <Button
                                    size="1"
                                    variant="soft"
                                    type="button"
                                    onClick={() => {
                                        const linkHtml = '<a href="[[Calendly Link]]">Schedule a meeting</a>';
                                        setTemplateForm({ 
                                            ...templateForm, 
                                            body: templateForm.body + '\n' + linkHtml 
                                        });
                                    }}
                                >
                                    + Calendly Link
                                </Button>
                                <Button
                                    size="1"
                                    variant="soft"
                                    type="button"
                                    onClick={() => {
                                        const linkHtml = '<a href="mailto:[[Associate email]]">Email me</a>';
                                        setTemplateForm({ 
                                            ...templateForm, 
                                            body: templateForm.body + '\n' + linkHtml 
                                        });
                                    }}
                                >
                                    + Email Link
                                </Button>
                            </Flex>
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