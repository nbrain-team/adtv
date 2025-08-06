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
}

export const ContactDataManager: React.FC<ContactDataManagerProps> = ({ 
    campaignId, 
    campaignName 
}) => {
    const [stats, setStats] = useState<ContactStats | null>(null);
    const [isLoadingStats, setIsLoadingStats] = useState(false);
    const [exportType, setExportType] = useState<'all' | 'incomplete'>('incomplete');
    const [mergeStrategy, setMergeStrategy] = useState<'update' | 'replace'>('update');
    const [isExporting, setIsExporting] = useState(false);
    const [isImporting, setIsImporting] = useState(false);
    const [importResult, setImportResult] = useState<any>(null);
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
        } finally {
            setIsLoadingStats(false);
        }
    };

    const handleExport = async () => {
        try {
            setIsExporting(true);
            
            let url = '';
            let filename = '';
            const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5);
            
            if (exportType === 'all') {
                url = `/api/campaigns/${campaignId}/export-all`;
                filename = `${campaignName}_all_contacts_${timestamp}.csv`;
            } else {
                // Export incomplete - automatically exports records missing email or phone
                url = `/api/campaigns/${campaignId}/export-incomplete?missing_fields=email,phone`;
                filename = `${campaignName}_incomplete_${timestamp}.csv`;
            }
            
            const response = await api.get(url, { responseType: 'blob' });

            // Create download link
            const downloadUrl = window.URL.createObjectURL(new Blob([response.data]));
            const link = document.createElement('a');
            link.href = downloadUrl;
            link.setAttribute('download', filename);
            document.body.appendChild(link);
            link.click();
            link.remove();
            window.URL.revokeObjectURL(downloadUrl);

            alert(`${exportType === 'all' ? 'All contacts' : 'Incomplete contacts'} exported successfully`);
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

        const formData = new FormData();
        formData.append('file', file);
        formData.append('merge_strategy', mergeStrategy);

        try {
            setIsImporting(true);
            setImportResult(null);
            
            const response = await api.post(
                `/api/campaigns/${campaignId}/reimport-contacts`,
                formData,
                {
                    headers: {
                        'Content-Type': 'multipart/form-data',
                    },
                }
            );

            setImportResult(response.data);
            fetchContactStats(); // Refresh stats after import
            alert(`Successfully updated ${response.data.updated_count} contacts`);
        } catch (error: any) {
            console.error('Import failed:', error);
            alert(error.response?.data?.detail || 'Failed to import contacts. Please try again.');
        } finally {
            setIsImporting(false);
            event.target.value = ''; // Reset file input
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

                {/* Export and Import Side by Side */}
                <Flex gap="4" wrap="wrap">
                    {/* Export Section */}
                    <Card variant="surface" style={{ flex: '1 1 300px' }}>
                        <Flex direction="column" gap="3" p="3">
                            <Text size="3" weight="bold">Export Contacts</Text>
                            
                            <Select.Root value={exportType} onValueChange={(value: 'all' | 'incomplete') => setExportType(value)}>
                                <Select.Trigger placeholder="Select export type" />
                                <Select.Content>
                                    <Select.Item value="incomplete">
                                        Export Incomplete (Missing Email/Phone)
                                    </Select.Item>
                                    <Select.Item value="all">
                                        Export All Contacts
                                    </Select.Item>
                                </Select.Content>
                            </Select.Root>
                            
                            <Button 
                                onClick={handleExport}
                                disabled={isExporting || !stats || stats.total_contacts === 0}
                                loading={isExporting}
                                size="2"
                            >
                                <Download className="w-4 h-4" />
                                Export {exportType === 'all' ? 'All' : 'Incomplete'}
                            </Button>
                        </Flex>
                    </Card>

                    {/* Import Section */}
                    <Card variant="surface" style={{ flex: '1 1 300px' }}>
                        <Flex direction="column" gap="3" p="3">
                            <Text size="3" weight="bold">Import Data</Text>
                            
                            <RadioGroup.Root value={mergeStrategy} onValueChange={(value: 'update' | 'replace') => setMergeStrategy(value)}>
                                <Flex direction="column" gap="2">
                                    <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                                        <RadioGroup.Item value="update" />
                                        <Text size="2">Update Empty Fields Only</Text>
                                    </label>
                                    <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                                        <RadioGroup.Item value="replace" />
                                        <Text size="2">Replace All Fields</Text>
                                    </label>
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
                                size="2"
                            >
                                <Upload className="w-4 h-4" />
                                Select CSV File
                            </Button>
                        </Flex>
                    </Card>
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
        </Card>
    );
}; 