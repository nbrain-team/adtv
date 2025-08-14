import React, { useState, useEffect, useRef } from 'react';
import { useParams } from 'react-router-dom';
import {
    Box, Card, Flex, Text, Button, TextField, Checkbox,
    Heading, Container
} from '@radix-ui/themes';
import { CheckCircledIcon, FileTextIcon } from '@radix-ui/react-icons';
import api from '../api';
import SignatureCanvas from 'react-signature-canvas';
const SigCanvas: any = SignatureCanvas as unknown as any;

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
    
    const [agreement, setAgreement] = useState<AgreementData | null>(null);
    const [loading, setLoading] = useState(true);
    const [signing, setSigning] = useState(false);
    const [signature, setSignature] = useState('');
    const signatureDate = new Date().toLocaleDateString();
    const [termsAccepted, setTermsAccepted] = useState(false);
    const [signatureType, setSignatureType] = useState<'typed' | 'drawn'>('typed');
    const [showSuccess, setShowSuccess] = useState(false);
    const sigPad = useRef<SignatureCanvas | null>(null);

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
        // Validate
        if (!termsAccepted) {
            alert('Please accept the terms to continue.');
            return;
        }
        if (signatureType === 'typed' && !signature) {
            alert('Please type your full name as your signature.');
            return;
        }
        if (signatureType === 'drawn' && (!sigPad.current || sigPad.current.isEmpty())) {
            alert('Please draw your signature.');
            return;
        }

        // Prepare payload
        let signaturePayload = signature;
        if (signatureType === 'drawn' && sigPad.current) {
            signaturePayload = sigPad.current.getTrimmedCanvas().toDataURL('image/png');
        }

        setSigning(true);
        try {
            await api.post(`/api/agreements/${agreementId}/sign`, {
                signature: signaturePayload,
                signature_type: signatureType,
                signed_date: signatureDate
            });

            setShowSuccess(true);
            setAgreement({ ...agreement!, status: 'signed', signature: signaturePayload });

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
        <div style={{ minHeight: '100vh' }}>
            <div style={{ position: 'relative' }}>
                <iframe
                    title="agreement-template"
                    src="/agreements/template.html"
                    style={{ width: '100%', height: '1800px', border: 'none', background: 'transparent' }}
                />
                {/* Overlay signature controls at the bottom to match template flow */}
                <div style={{ position: 'absolute', left: 0, right: 0, bottom: 24, display: 'flex', justifyContent: 'center' }}>
                    <Card style={{ maxWidth: 900, width: '95%', padding: 16 }}>
                        <Flex direction="column" gap="3">
                            <Flex gap="2">
                                <Button variant={signatureType === 'typed' ? 'solid' : 'soft'} onClick={() => setSignatureType('typed')}>Type</Button>
                                <Button variant={signatureType === 'drawn' ? 'solid' : 'soft'} onClick={() => setSignatureType('drawn')}>Draw</Button>
                            </Flex>
                            {signatureType === 'typed' ? (
                                <TextField.Root
                                    size="3"
                                    placeholder="Type your full legal name"
                                    value={signature}
                                    onChange={(e) => setSignature(e.target.value)}
                                    style={{ fontFamily: 'cursive', fontSize: '1.5rem', fontStyle: 'italic' }}
                                />
                            ) : (
                                <Box style={{ backgroundColor: 'white', border: '1px solid var(--gray-5)', borderRadius: 8, padding: 8 }}>
                                    <SigCanvas
                                        ref={sigPad}
                                        penColor="#111"
                                        canvasProps={{ width: 800, height: 200, style: { width: '100%', height: 200 } }}
                                    />
                                    <Flex mt="2" gap="2">
                                        <Button variant="soft" onClick={() => sigPad.current?.clear()}>Clear</Button>
                                    </Flex>
                                </Box>
                            )}
                            <Flex align="center" gap="2">
                                <Checkbox checked={termsAccepted} onCheckedChange={(c) => setTermsAccepted(c as boolean)} />
                                <Text size="2">I agree to the terms and conditions</Text>
                            </Flex>
                            <Flex justify="end" gap="3">
                                <Button variant="soft" onClick={() => window.print()}>Print</Button>
                                <Button
                                    disabled={(!termsAccepted) || (signatureType === 'typed' && !signature) || (signatureType === 'drawn' && !!sigPad.current && sigPad.current.isEmpty()) || signing}
                                    onClick={handleSign}
                                >
                                    {signing ? 'Signing...' : 'Sign Agreement'}
                                </Button>
                            </Flex>
                        </Flex>
                    </Card>
                </div>
            </div>
        </div>
    );
}; 