import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
    Box, Card, Flex, Text, Button, TextField, Checkbox,
    Heading, Separator, Badge, Container
} from '@radix-ui/themes';
import { CheckCircledIcon, FileTextIcon, CalendarIcon } from '@radix-ui/react-icons';
import api from '../api';

interface AgreementData {
    id: string;
    contact_name: string;
    contact_email: string;
    company: string;
    start_date: string;
    setup_fee: string;
    monthly_fee: string;
    campaign_name: string;
    status: 'pending' | 'viewed' | 'signed';
    signed_at?: string;
    signature?: string;
}

export const AgreementSigningPage: React.FC = () => {
    const { agreementId } = useParams<{ agreementId: string }>();
    const navigate = useNavigate();
    
    const [agreement, setAgreement] = useState<AgreementData | null>(null);
    const [loading, setLoading] = useState(true);
    const [signing, setSigning] = useState(false);
    const [signature, setSignature] = useState('');
    const [signatureDate, setSignatureDate] = useState(new Date().toLocaleDateString());
    const [termsAccepted, setTermsAccepted] = useState(false);
    const [signatureType, setSignatureType] = useState<'typed' | 'drawn'>('typed');
    const [showSuccess, setShowSuccess] = useState(false);

    useEffect(() => {
        if (agreementId) {
            fetchAgreement();
        }
    }, [agreementId]);

    const fetchAgreement = async () => {
        try {
            const response = await api.get(`/api/agreements/${agreementId}`);
            setAgreement(response.data);
            
            // Mark as viewed if still pending
            if (response.data.status === 'pending') {
                await api.post(`/api/agreements/${agreementId}/view`);
            }
        } catch (error) {
            console.error('Error fetching agreement:', error);
            // Show error page
        } finally {
            setLoading(false);
        }
    };

    const handleSign = async () => {
        if (!signature || !termsAccepted) {
            alert('Please provide your signature and accept the terms.');
            return;
        }

        setSigning(true);
        try {
            const response = await api.post(`/api/agreements/${agreementId}/sign`, {
                signature,
                signature_type: signatureType,
                signed_date: signatureDate
            });

            setShowSuccess(true);
            setAgreement({ ...agreement!, status: 'signed', signature });

            // Download PDF automatically
            const pdfResponse = await api.get(`/api/agreements/${agreementId}/pdf`, {
                responseType: 'blob'
            });
            
            const url = window.URL.createObjectURL(new Blob([pdfResponse.data]));
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', `agreement_${agreementId}.pdf`);
            document.body.appendChild(link);
            link.click();
            link.remove();

        } catch (error) {
            console.error('Error signing agreement:', error);
            alert('Failed to sign agreement. Please try again.');
        } finally {
            setSigning(false);
        }
    };

    if (loading) {
        return (
            <Container size="2" style={{ padding: '2rem' }}>
                <Card>
                    <Flex justify="center" align="center" style={{ height: '400px' }}>
                        <Text>Loading agreement...</Text>
                    </Flex>
                </Card>
            </Container>
        );
    }

    if (!agreement) {
        return (
            <Container size="2" style={{ padding: '2rem' }}>
                <Card>
                    <Flex direction="column" align="center" gap="4" style={{ padding: '3rem' }}>
                        <Text size="5" weight="bold">Agreement Not Found</Text>
                        <Text color="gray">This agreement link may be invalid or expired.</Text>
                    </Flex>
                </Card>
            </Container>
        );
    }

    if (agreement.status === 'signed') {
        return (
            <Container size="2" style={{ padding: '2rem' }}>
                <Card>
                    <Flex direction="column" align="center" gap="4" style={{ padding: '3rem' }}>
                        <CheckCircledIcon style={{ width: 60, height: 60, color: 'var(--green-9)' }} />
                        <Text size="5" weight="bold">Agreement Already Signed</Text>
                        <Text color="gray">This agreement was signed on {agreement.signed_at}</Text>
                        <Button onClick={() => window.location.href = `/api/agreements/${agreementId}/pdf`}>
                            Download PDF
                        </Button>
                    </Flex>
                </Card>
            </Container>
        );
    }

    if (showSuccess) {
        return (
            <Container size="2" style={{ padding: '2rem' }}>
                <Card>
                    <Flex direction="column" align="center" gap="4" style={{ padding: '3rem' }}>
                        <CheckCircledIcon style={{ width: 60, height: 60, color: 'var(--green-9)' }} />
                        <Heading size="6">Agreement Successfully Signed!</Heading>
                        <Text align="center" color="gray">
                            Thank you for signing the agreement. A copy has been sent to your email and downloaded to your device.
                        </Text>
                        <Flex gap="3">
                            <Button 
                                variant="soft"
                                onClick={() => window.location.href = `/api/agreements/${agreementId}/pdf`}
                            >
                                <FileTextIcon />
                                Download PDF Again
                            </Button>
                        </Flex>
                    </Flex>
                </Card>
            </Container>
        );
    }

    return (
        <Container size="3" style={{ padding: '2rem' }}>
            <Card>
                {/* Header */}
                <Box style={{ padding: '2rem', backgroundColor: 'var(--blue-2)', borderBottom: '1px solid var(--gray-4)' }}>
                    <Flex align="center" justify="between">
                        <Box>
                            <Heading size="7">Service Agreement</Heading>
                            <Text size="3" color="gray" style={{ marginTop: '0.5rem' }}>
                                {agreement.campaign_name}
                            </Text>
                        </Box>
                        <Badge size="2" color="blue">
                            <CalendarIcon />
                            {agreement.start_date}
                        </Badge>
                    </Flex>
                </Box>

                {/* Agreement Content */}
                <Box style={{ padding: '2rem' }}>
                    <Flex direction="column" gap="4">
                        {/* Party Information */}
                        <Box>
                            <Heading size="4" mb="3">Agreement Between</Heading>
                            <Card style={{ backgroundColor: 'var(--gray-1)' }}>
                                <Flex direction="column" gap="2">
                                    <Flex justify="between">
                                        <Text weight="medium">Service Provider:</Text>
                                        <Text>ADTV Corporation</Text>
                                    </Flex>
                                    <Flex justify="between">
                                        <Text weight="medium">Client:</Text>
                                        <Text>{agreement.contact_name}</Text>
                                    </Flex>
                                    <Flex justify="between">
                                        <Text weight="medium">Company:</Text>
                                        <Text>{agreement.company || 'N/A'}</Text>
                                    </Flex>
                                    <Flex justify="between">
                                        <Text weight="medium">Email:</Text>
                                        <Text>{agreement.contact_email}</Text>
                                    </Flex>
                                </Flex>
                            </Card>
                        </Box>

                        <Separator />

                        {/* Service Details */}
                        <Box>
                            <Heading size="4" mb="3">Service Details</Heading>
                            <Card style={{ backgroundColor: 'var(--gray-1)' }}>
                                <Flex direction="column" gap="3">
                                    <Box>
                                        <Text size="2" weight="medium" color="gray">Service Type</Text>
                                        <Text size="3">ADTV Marketing & Advertising Services</Text>
                                    </Box>
                                    <Box>
                                        <Text size="2" weight="medium" color="gray">Service Start Date</Text>
                                        <Text size="3">{agreement.start_date}</Text>
                                    </Box>
                                </Flex>
                            </Card>
                        </Box>

                        <Separator />

                        {/* Pricing */}
                        <Box>
                            <Heading size="4" mb="3">Investment</Heading>
                            <Card style={{ backgroundColor: 'var(--blue-1)' }}>
                                <Flex direction="column" gap="3">
                                    <Flex justify="between" align="center">
                                        <Box>
                                            <Text weight="medium">One-time Setup Fee</Text>
                                            <Text size="1" color="gray">Due upon signing</Text>
                                        </Box>
                                        <Text size="5" weight="bold">${agreement.setup_fee}</Text>
                                    </Flex>
                                    <Separator />
                                    <Flex justify="between" align="center">
                                        <Box>
                                            <Text weight="medium">Monthly Service Fee</Text>
                                            <Text size="1" color="gray">Recurring monthly charge</Text>
                                        </Box>
                                        <Text size="5" weight="bold">${agreement.monthly_fee}/mo</Text>
                                    </Flex>
                                </Flex>
                            </Card>
                        </Box>

                        <Separator />

                        {/* Terms & Conditions */}
                        <Box>
                            <Heading size="4" mb="3">Terms & Conditions</Heading>
                            <Card style={{ backgroundColor: 'var(--gray-1)', maxHeight: '300px', overflow: 'auto' }}>
                                <Text size="2" style={{ lineHeight: 1.6 }}>
                                    <strong>1. Services:</strong> ADTV Corporation ("Provider") agrees to provide marketing and advertising services as outlined in the campaign details.<br/><br/>
                                    
                                    <strong>2. Payment Terms:</strong> Client agrees to pay the one-time setup fee upon signing this agreement and the monthly service fee on a recurring basis. Payments are due on the same date each month.<br/><br/>
                                    
                                    <strong>3. Term:</strong> This agreement shall commence on the Start Date specified above and continue on a month-to-month basis until terminated by either party with 30 days written notice.<br/><br/>
                                    
                                    <strong>4. Cancellation:</strong> Either party may cancel this agreement with 30 days written notice. Setup fees are non-refundable. Monthly fees are prorated based on the cancellation date.<br/><br/>
                                    
                                    <strong>5. Confidentiality:</strong> Both parties agree to maintain confidentiality of proprietary information shared during the course of this agreement.<br/><br/>
                                    
                                    <strong>6. Liability:</strong> Provider's liability is limited to the amount of fees paid by Client in the preceding month.<br/><br/>
                                    
                                    <strong>7. Governing Law:</strong> This agreement shall be governed by the laws of the state in which the Provider is incorporated.
                                </Text>
                            </Card>
                        </Box>

                        <Separator />

                        {/* Signature Section */}
                        <Box>
                            <Heading size="4" mb="3">Electronic Signature</Heading>
                            <Card style={{ backgroundColor: 'var(--gray-1)' }}>
                                <Flex direction="column" gap="3">
                                    <Box>
                                        <Text size="2" weight="medium" mb="2">
                                            Type your full legal name to sign this agreement
                                        </Text>
                                        <TextField.Root
                                            size="3"
                                            placeholder="Enter your full name"
                                            value={signature}
                                            onChange={(e) => setSignature(e.target.value)}
                                            style={{ 
                                                fontFamily: 'cursive', 
                                                fontSize: '1.5rem',
                                                fontStyle: 'italic'
                                            }}
                                        />
                                    </Box>
                                    
                                    <Box>
                                        <Text size="2" color="gray">
                                            Signing Date: {signatureDate}
                                        </Text>
                                    </Box>

                                    <Box>
                                        <Flex align="center" gap="2">
                                            <Checkbox 
                                                checked={termsAccepted}
                                                onCheckedChange={(checked) => setTermsAccepted(checked as boolean)}
                                            />
                                            <Text size="2">
                                                I have read and agree to the terms and conditions of this agreement
                                            </Text>
                                        </Flex>
                                    </Box>
                                </Flex>
                            </Card>
                        </Box>

                        {/* Action Buttons */}
                        <Flex gap="3" justify="end" mt="4">
                            <Button 
                                size="3"
                                variant="soft"
                                onClick={() => window.print()}
                            >
                                Print Agreement
                            </Button>
                            <Button 
                                size="3"
                                disabled={!signature || !termsAccepted || signing}
                                onClick={handleSign}
                            >
                                {signing ? 'Signing...' : 'Sign Agreement'}
                            </Button>
                        </Flex>
                    </Flex>
                </Box>
            </Card>
        </Container>
    );
}; 