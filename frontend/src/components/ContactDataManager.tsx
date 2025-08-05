import React, { useState, useRef, useEffect } from 'react';
import { 
    Card, 
    Flex, 
    Text, 
    Button, 
    Dialog,
    Select,
    RadioGroup,
    Badge,
    Callout,
    Separator,
    Spinner,
    Strong
} from '@radix-ui/themes';
import { 
    Upload, 
    Download, 
    FileSpreadsheet, 
    AlertCircle, 
    CheckCircle,
    Users,
    Mail,
    Phone,
    AlertTriangle
} from 'lucide-react';
import api from '../services/api';

interface ContactStats {
    total_contacts: number;
    contacts_with_email: number;
    contacts_with_phone: number;
    contacts_missing_both: number;
    contacts_missing_email: number;
    contacts_missing_phone: number;
    email_coverage_percentage: number;
    phone_coverage_percentage: number;
}

interface ContactDataManagerProps {
    campaignId: string;
    campaignName: string;
    onDataUpdate?: () => void;
}

export const ContactDataManager: React.FC<ContactDataManagerProps> = ({ 
    campaignId, 
    campaignName,
    onDataUpdate 
}) => {
    const [stats, setStats] = useState<ContactStats | null>(null);
    const [isLoadingStats, setIsLoadingStats] = useState(false);
    const [exportFields, setExportFields] = useState('email,phone');
    const [mergeStrategy, setMergeStrategy] = useState('update');
    const [isExporting, setIsExporting] = useState(false);
    const [isImporting, setIsImporting] = useState(false);
    const [importResult, setImportResult] = useState<any>(null);
    const [showImportDialog, setShowImportDialog] = useState(false);
    const fileInputRef = useRef<HTMLInputElement>(null);

    useEffect(() => {
        fetchContactStats();
    }, [campaignId]);

    const fetchContactStats = async () => {
        try {
            setIsLoadingStats(true);
            const response = await api.get(`/api/campaigns/${campaignId}/contacts/stats`);
            setStats(response.data);
        } catch (error) {
            console.error('Failed to fetch contact stats:', error);
            // Silent fail - stats will just not show
        } finally {
            setIsLoadingStats(false);
        }
    };

    const handleExportIncomplete = async () => {
        try {
            setIsExporting(true);
            const response = await api.get(
                `/api/campaigns/${campaignId}/export-incomplete?missing_fields=${exportFields}`,
                { responseType: 'blob' }
            );

            // Create download link
            const url = window.URL.createObjectURL(new Blob([response.data]));
            const link = document.createElement('a');
            link.href = url;
            const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5);
            link.setAttribute('download', `${campaignName}_incomplete_${timestamp}.csv`);
            document.body.appendChild(link);
            link.click();
            link.remove();
            window.URL.revokeObjectURL(url);

            alert('Incomplete contacts exported successfully');
        } catch (error) {
            console.error('Export failed:', error);
            alert('Failed to export contacts. Please try again.');
        } finally {
            setIsExporting(false);
        }
    };

    const handleExportAll = async () => {
        try {
            setIsExporting(true);
            const response = await api.get(
                `/api/campaigns/${campaignId}/export-all`,
                { responseType: 'blob' }
            );

            // Create download link
            const url = window.URL.createObjectURL(new Blob([response.data]));
            const link = document.createElement('a');
            link.href = url;
            const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5);
            link.setAttribute('download', `${campaignName}_all_contacts_${timestamp}.csv`);
            document.body.appendChild(link);
            link.click();
            link.remove();
            window.URL.revokeObjectURL(url);

            alert('All contacts exported successfully');
        } catch (error) {
            console.error('Export failed:', error);
            alert('Failed to export contacts. Please try again.');
        } finally {
            setIsExporting(false);
        }
    };

    const handleFileSelect = async (event: React.ChangeEvent<HTMLInputElement>) => {
        const file = event.target.files?.[0];
        if (!file) return;

        if (!file.name.endsWith('.csv')) {
            alert('Please select a CSV file');
            return;
        }

        try {
            setIsImporting(true);
            const formData = new FormData();
            formData.append('file', file);

            const response = await api.post(
                `/api/campaigns/${campaignId}/reimport-contacts?merge_strategy=${mergeStrategy}`,
                formData,
                {
                    headers: {
                        'Content-Type': 'multipart/form-data',
                    },
                }
            );

            setImportResult(response.data);
            
            if (response.data.success) {
                alert(`Successfully updated ${response.data.updated_count} contacts`);
                
                // Refresh stats
                await fetchContactStats();
                
                // Notify parent component
                if (onDataUpdate) {
                    onDataUpdate();
                }
            }
        } catch (error: any) {
            console.error('Import failed:', error);
            alert(error.response?.data?.detail || 'Failed to import contacts. Please try again.');
        } finally {
            setIsImporting(false);
            if (fileInputRef.current) {
                fileInputRef.current.value = '';
            }
        }
    };

    const getCoverageColor = (percentage: number) => {
        if (percentage >= 90) return 'green';
        if (percentage >= 70) return 'yellow';
        if (percentage >= 50) return 'orange';
        return 'red';
    };

    return (
        <Card size="3">
            <Flex direction="column" gap="4">
                <Flex justify="between" align="center">
                    <Flex direction="column" gap="1">
                        <Text size="5" weight="bold">Contact Data Manager</Text>
                        <Text size="2" color="gray">Export incomplete records, enrich offline, and re-import</Text>
                    </Flex>
                    <Badge size="2" variant="soft">
                        <Users className="w-3 h-3" />
                        {stats?.total_contacts || 0} Total Contacts
                    </Badge>
                </Flex>

                <Separator size="4" />

                {/* Statistics Section */}
                {isLoadingStats ? (
                    <Flex justify="center" py="4">
                        <Spinner />
                    </Flex>
                ) : stats && (
                    <Flex direction="column" gap="3">
                        <Text size="3" weight="bold">Data Coverage</Text>
                        
                        <Flex gap="3" wrap="wrap">
                            <Card variant="surface">
                                <Flex direction="column" gap="2" p="2">
                                    <Flex align="center" gap="2">
                                        <Mail className="w-4 h-4" />
                                        <Text size="2" weight="bold">Email Coverage</Text>
                                    </Flex>
                                    <Flex align="baseline" gap="2">
                                        <Text size="5" weight="bold">
                                            {stats.email_coverage_percentage}%
                                        </Text>
                                        <Badge color={getCoverageColor(stats.email_coverage_percentage)} variant="soft">
                                            {stats.contacts_with_email} / {stats.total_contacts}
                                        </Badge>
                                    </Flex>
                                    <Text size="1" color="gray">
                                        Missing: {stats.contacts_missing_email} contacts
                                    </Text>
                                </Flex>
                            </Card>

                            <Card variant="surface">
                                <Flex direction="column" gap="2" p="2">
                                    <Flex align="center" gap="2">
                                        <Phone className="w-4 h-4" />
                                        <Text size="2" weight="bold">Phone Coverage</Text>
                                    </Flex>
                                    <Flex align="baseline" gap="2">
                                        <Text size="5" weight="bold">
                                            {stats.phone_coverage_percentage}%
                                        </Text>
                                        <Badge color={getCoverageColor(stats.phone_coverage_percentage)} variant="soft">
                                            {stats.contacts_with_phone} / {stats.total_contacts}
                                        </Badge>
                                    </Flex>
                                    <Text size="1" color="gray">
                                        Missing: {stats.contacts_missing_phone} contacts
                                    </Text>
                                </Flex>
                            </Card>

                            {stats.contacts_missing_both > 0 && (
                                <Card variant="surface">
                                    <Flex direction="column" gap="2" p="2">
                                        <Flex align="center" gap="2">
                                            <AlertTriangle className="w-4 h-4 text-orange-500" />
                                            <Text size="2" weight="bold">Missing Both</Text>
                                        </Flex>
                                        <Text size="5" weight="bold" color="orange">
                                            {stats.contacts_missing_both}
                                        </Text>
                                        <Text size="1" color="gray">
                                            contacts need data
                                        </Text>
                                    </Flex>
                                </Card>
                            )}
                        </Flex>
                    </Flex>
                )}

                <Separator size="4" />

                {/* Export Section */}
                <Flex direction="column" gap="3">
                    <Text size="3" weight="bold">Export Contacts</Text>
                    
                    <Flex gap="3" wrap="wrap">
                        {/* Export Incomplete */}
                        <Card variant="surface">
                            <Flex direction="column" gap="3" p="3">
                                <Text size="2" weight="bold">Export Incomplete</Text>
                                <Flex direction="column" gap="2">
                                    <Text size="2">Export contacts missing:</Text>
                                    <Select.Root value={exportFields} onValueChange={setExportFields}>
                                        <Select.Trigger />
                                        <Select.Content>
                                            <Select.Item value="email">Email only</Select.Item>
                                            <Select.Item value="phone">Phone only</Select.Item>
                                            <Select.Item value="email,phone">Email or Phone</Select.Item>
                                        </Select.Content>
                                    </Select.Root>
                                </Flex>
                                <Button 
                                    onClick={handleExportIncomplete}
                                    disabled={isExporting || !stats || stats.total_contacts === 0}
                                    loading={isExporting}
                                    size="2"
                                >
                                    <Download className="w-4 h-4" />
                                    Export Incomplete
                                </Button>
                            </Flex>
                        </Card>

                        {/* Export All */}
                        <Card variant="surface">
                            <Flex direction="column" gap="3" p="3">
                                <Text size="2" weight="bold">Export All</Text>
                                <Text size="1" color="gray">
                                    Download complete contact list with all fields for backup or analysis
                                </Text>
                                <Button 
                                    onClick={handleExportAll}
                                    disabled={isExporting || !stats || stats.total_contacts === 0}
                                    loading={isExporting}
                                    variant="soft"
                                    size="2"
                                >
                                    <FileSpreadsheet className="w-4 h-4" />
                                    Export All Contacts
                                </Button>
                            </Flex>
                        </Card>
                    </Flex>

                    {stats && (stats.contacts_missing_email > 0 || stats.contacts_missing_phone > 0) && (
                        <Callout.Root size="1" color="blue">
                            <Callout.Icon>
                                <AlertCircle />
                            </Callout.Icon>
                            <Callout.Text>
                                The exported CSV will include all contact fields and a unique ID for each record. 
                                After enriching the data offline, you can re-import the same file to update the contacts.
                            </Callout.Text>
                        </Callout.Root>
                    )}
                </Flex>

                <Separator size="4" />

                {/* Import Section */}
                <Flex direction="column" gap="3">
                    <Text size="3" weight="bold">Re-import Enriched Data</Text>
                    
                    <Flex direction="column" gap="3">
                        <RadioGroup.Root value={mergeStrategy} onValueChange={setMergeStrategy}>
                            <Flex direction="column" gap="2">
                                <Text size="2">Merge Strategy:</Text>
                                <Flex direction="column" gap="2">
                                    <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                                        <RadioGroup.Item value="update" />
                                        <Flex direction="column">
                                            <Text size="2" weight="bold">Update Empty Fields Only</Text>
                                            <Text size="1" color="gray">Only fill in missing data, preserve existing values</Text>
                                        </Flex>
                                    </label>
                                    <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                                        <RadioGroup.Item value="replace" />
                                        <Flex direction="column">
                                            <Text size="2" weight="bold">Replace All Fields</Text>
                                            <Text size="1" color="gray">Overwrite all fields with imported values</Text>
                                        </Flex>
                                    </label>
                                </Flex>
                            </Flex>
                        </RadioGroup.Root>

                        <input
                            ref={fileInputRef}
                            type="file"
                            accept=".csv"
                            onChange={handleFileSelect}
                            style={{ display: 'none' }}
                        />

                        <Button
                            onClick={() => fileInputRef.current?.click()}
                            disabled={isImporting}
                            loading={isImporting}
                            variant="soft"
                        >
                            <Upload className="w-4 h-4" />
                            Select CSV File to Import
                        </Button>
                    </Flex>

                    {/* Import Results */}
                    {importResult && (
                        <Callout.Root 
                            size="2" 
                            color={importResult.error_count > 0 ? "orange" : "green"}
                        >
                            <Callout.Icon>
                                {importResult.error_count > 0 ? <AlertTriangle /> : <CheckCircle />}
                            </Callout.Icon>
                            <Callout.Text>
                                <Flex direction="column" gap="1">
                                    <Strong>Import Complete</Strong>
                                    <Text size="2">
                                        • Updated: {importResult.updated_count} contacts<br />
                                        • Not Found: {importResult.not_found_count} IDs<br />
                                        • Errors: {importResult.error_count}
                                    </Text>
                                    {importResult.errors && importResult.errors.length > 0 && (
                                        <Text size="1" color="orange">
                                            {importResult.errors[0]}
                                        </Text>
                                    )}
                                </Flex>
                            </Callout.Text>
                        </Callout.Root>
                    )}
                </Flex>
            </Flex>
        </Card>
    );
}; 