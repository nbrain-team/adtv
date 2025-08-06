import React, { useState } from 'react';
import {
    Dialog, Box, Flex, Text, Button, TextField, 
    TextArea, Separator, Badge, Card
} from '@radix-ui/themes';
import { FileTextIcon, PaperPlaneIcon } from '@radix-ui/react-icons';
import api from '../api';

interface Contact {
    id: string;
    first_name?: string;
    last_name?: string;
    email?: string;
    company?: string;
    phone?: string;
    is_rsvp?: boolean;
    rsvp_status?: string;
}

interface RSVPAgreementModalProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    selectedContacts: Contact[];
    campaignId: string;
    campaignName: string;
}

export const RSVPAgreementModal: React.FC<RSVPAgreementModalProps> = ({
    open,
    onOpenChange,
    selectedContacts,
    campaignId,
    campaignName
}) => {
    const [agreementData, setAgreementData] = useState({
        startDate: new Date().toISOString().split('T')[0],
        setupFee: '1495',
        monthlyFee: '1595',
        emailSubject: 'Your ADTV Agreement is Ready for Signature',
        emailBody: `Hi {{FirstName}},

Thank you for your interest in partnering with ADTV. Your personalized agreement is ready for review and signature.

Please click the link below to review and sign your agreement:
{{AgreementLink}}

This agreement includes:
- Start Date: {{StartDate}}
- One-time Setup Fee: $` + `{{SetupFee}}` + `
- Monthly Recurring Fee: $` + `{{MonthlyFee}}` + `

If you have any questions, please don't hesitate to reach out.

Best regards,
The ADTV Team`,
        agreementTemplate: 'standard' // We can have multiple templates
    });

    const [isSending, setIsSending] = useState(false);

    const handleSendAgreements = async () => {
        if (!selectedContacts.length) {
            alert('No contacts selected');
            return;
        }

        const missingEmails = selectedContacts.filter(c => !c.email);
        if (missingEmails.length > 0) {
            alert(`${missingEmails.length} contacts are missing email addresses. Please update them first.`);
            return;
        }

        setIsSending(true);
        
        try {
            const payload = {
                contact_ids: selectedContacts.map(c => c.id),
                agreement_data: {
                    start_date: agreementData.startDate,
                    setup_fee: agreementData.setupFee,
                    monthly_fee: agreementData.monthlyFee,
                    email_subject: agreementData.emailSubject,
                    email_body: agreementData.emailBody,
                    template: agreementData.agreementTemplate
                }
            };

            const response = await api.post(`/api/campaigns/${campaignId}/send-agreements`, payload);
            
            alert(`Successfully sent agreements to ${selectedContacts.length} contacts!`);
            onOpenChange(false);
            
            // Reset form
            setAgreementData({
                startDate: new Date().toISOString().split('T')[0],
                setupFee: '1495',
                monthlyFee: '1595',
                emailSubject: 'Your ADTV Agreement is Ready for Signature',
                emailBody: agreementData.emailBody,
                agreementTemplate: 'standard'
            });
            
        } catch (error: any) {
            console.error('Error sending agreements:', error);
            alert(`Failed to send agreements: ${error.response?.data?.detail || error.message}`);
        } finally {
            setIsSending(false);
        }
    };

    const previewMerge = (text: string): string => {
        const firstContact = selectedContacts[0];
        if (!firstContact) return text;
        
        return text
            .replace(/{{FirstName}}/g, firstContact.first_name || '[First Name]')
            .replace(/{{LastName}}/g, firstContact.last_name || '[Last Name]')
            .replace(/{{Email}}/g, firstContact.email || '[Email]')
            .replace(/{{Company}}/g, firstContact.company || '[Company]')
            .replace(/{{StartDate}}/g, agreementData.startDate)
            .replace(/{{SetupFee}}/g, agreementData.setupFee)
            .replace(/{{MonthlyFee}}/g, agreementData.monthlyFee)
            .replace(/{{AgreementLink}}/g, '[Agreement Link Will Be Here]');
    };

    return (
        <Dialog.Root open={open} onOpenChange={onOpenChange}>
            <Dialog.Content style={{ maxWidth: 700, maxHeight: '90vh', overflowY: 'auto' }}>
                <Dialog.Title>
                    <Flex align="center" gap="2">
                        <FileTextIcon />
                        Send E-Signature Agreements
                    </Flex>
                </Dialog.Title>
                <Dialog.Description>
                    Configure and send agreements for e-signature to selected RSVP contacts
                </Dialog.Description>

                <Flex direction="column" gap="4" mt="4">
                    {/* Selected Contacts Summary */}
                    <Box style={{ padding: '12px', backgroundColor: 'var(--blue-1)' }}>
                        <Flex justify="between" align="center">
                            <Text size="2">
                                <strong>Selected Contacts:</strong> {selectedContacts.length}
                            </Text>
                            {selectedContacts.length > 0 && (
                                <Badge color="blue">
                                    {selectedContacts.filter(c => c.email).length} with email
                                </Badge>
                            )}
                        </Flex>
                        {selectedContacts.length > 0 && (
                            <Box mt="2">
                                <Text size="1" color="gray">
                                    {selectedContacts.slice(0, 3).map(c => 
                                        `${c.first_name} ${c.last_name}`
                                    ).join(', ')}
                                    {selectedContacts.length > 3 && `, and ${selectedContacts.length - 3} more...`}
                                </Text>
                            </Box>
                        )}
                    </Box>

                    <Separator />

                    {/* Agreement Configuration */}
                    <Box>
                        <Text size="3" weight="bold" mb="3">Agreement Details</Text>
                        
                        <Flex direction="column" gap="3">
                            <Box>
                                <Text as="label" size="2" weight="medium" mb="1">
                                    Agreement Start Date
                                </Text>
                                <TextField.Root
                                    type="date"
                                    value={agreementData.startDate}
                                    onChange={(e) => setAgreementData({
                                        ...agreementData,
                                        startDate: e.target.value
                                    })}
                                />
                            </Box>

                            <Flex gap="3">
                                <Box style={{ flex: 1 }}>
                                    <Text as="label" size="2" weight="medium" mb="1">
                                        One-time Setup Fee ($)
                                    </Text>
                                    <TextField.Root
                                        type="number"
                                        value={agreementData.setupFee}
                                        onChange={(e) => setAgreementData({
                                            ...agreementData,
                                            setupFee: e.target.value
                                        })}
                                    />
                                </Box>

                                <Box style={{ flex: 1 }}>
                                    <Text as="label" size="2" weight="medium" mb="1">
                                        Monthly Recurring Fee ($)
                                    </Text>
                                    <TextField.Root
                                        type="number"
                                        value={agreementData.monthlyFee}
                                        onChange={(e) => setAgreementData({
                                            ...agreementData,
                                            monthlyFee: e.target.value
                                        })}
                                    />
                                </Box>
                            </Flex>
                        </Flex>
                    </Box>

                    <Separator />

                    {/* Email Configuration */}
                    <Box>
                        <Text size="3" weight="bold" mb="3">Email Configuration</Text>
                        
                        <Flex direction="column" gap="3">
                            <Box>
                                <Text as="label" size="2" weight="medium" mb="1">
                                    Email Subject
                                </Text>
                                <TextField.Root
                                    value={agreementData.emailSubject}
                                    onChange={(e) => setAgreementData({
                                        ...agreementData,
                                        emailSubject: e.target.value
                                    })}
                                />
                            </Box>

                            <Box>
                                <Text as="label" size="2" weight="medium" mb="1">
                                    Email Body
                                </Text>
                                <TextArea
                                    value={agreementData.emailBody}
                                    onChange={(e) => setAgreementData({
                                        ...agreementData,
                                        emailBody: e.target.value
                                    })}
                                    rows={8}
                                    style={{ fontFamily: 'monospace', fontSize: '12px' }}
                                />
                                <Text size="1" color="gray" mt="1">
                                    Available merge fields: {'{{FirstName}}'}, {'{{LastName}}'}, {'{{Email}}'}, 
                                    {'{{Company}}'}, {'{{StartDate}}'}, {'{{SetupFee}}'}, {'{{MonthlyFee}}'}, {'{{AgreementLink}}'}
                                </Text>
                            </Box>
                        </Flex>
                    </Box>

                    {/* Preview */}
                    {selectedContacts.length > 0 && (
                        <>
                            <Separator />
                            <Box>
                                <Text size="3" weight="bold" mb="3">
                                    Preview (using first selected contact)
                                </Text>
                                <Box style={{ padding: '12px', backgroundColor: 'var(--gray-1)' }}>
                                    <Text size="2" weight="medium">Subject:</Text>
                                    <Text size="2" style={{ marginBottom: '8px' }}>
                                        {previewMerge(agreementData.emailSubject)}
                                    </Text>
                                    <Text size="2" weight="medium">Body:</Text>
                                    <Text size="2" style={{ whiteSpace: 'pre-wrap' }}>
                                        {previewMerge(agreementData.emailBody)}
                                    </Text>
                                </Box>
                            </Box>
                        </>
                    )}

                    {/* Actions */}
                    <Flex gap="3" justify="end">
                        <Dialog.Close>
                            <Button variant="soft">Cancel</Button>
                        </Dialog.Close>
                        <Button 
                            onClick={handleSendAgreements}
                            disabled={isSending || selectedContacts.length === 0}
                        >
                            {isSending ? 'Sending...' : (
                                <>
                                    <PaperPlaneIcon />
                                    Send Agreements ({selectedContacts.length})
                                </>
                            )}
                        </Button>
                    </Flex>
                </Flex>
            </Dialog.Content>
        </Dialog.Root>
    );
}; 