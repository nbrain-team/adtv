import { useState, useEffect } from 'react';
import { Box, Flex, Heading, Text, Card, TextField, Button, Callout } from '@radix-ui/themes';
import { InfoCircledIcon, PersonIcon } from '@radix-ui/react-icons';
import { MainLayout } from '../components/MainLayout';
import api from '../api';

interface UserProfile {
    id: string;
    email: string;
    first_name: string | null;
    last_name: string | null;
    company: string | null;
    website_url: string | null;
    role: string;
    created_at: string;
    last_login: string | null;
}

const ProfilePage = () => {
    const [profile, setProfile] = useState<UserProfile | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [isEditing, setIsEditing] = useState(false);
    const [isSaving, setIsSaving] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState<string | null>(null);
    
    // Form state
    const [formData, setFormData] = useState({
        first_name: '',
        last_name: '',
        company: '',
        website_url: ''
    });

    useEffect(() => {
        fetchProfile();
    }, []);

    const fetchProfile = async () => {
        try {
            const response = await api.get('/user/profile');
            setProfile(response.data);
            setFormData({
                first_name: response.data.first_name || '',
                last_name: response.data.last_name || '',
                company: response.data.company || '',
                website_url: response.data.website_url || ''
            });
        } catch (err) {
            setError('Failed to load profile');
        } finally {
            setIsLoading(false);
        }
    };

    const handleSave = async () => {
        setIsSaving(true);
        setError(null);
        setSuccess(null);
        
        try {
            await api.put('/user/profile', formData);
            await fetchProfile();
            setIsEditing(false);
            setSuccess('Profile updated successfully!');
        } catch (err) {
            setError('Failed to update profile');
        } finally {
            setIsSaving(false);
        }
    };

    const handleCancel = () => {
        setIsEditing(false);
        if (profile) {
            setFormData({
                first_name: profile.first_name || '',
                last_name: profile.last_name || '',
                company: profile.company || '',
                website_url: profile.website_url || ''
            });
        }
    };

    return (
        <MainLayout onNewChat={() => {}}>
            <Box style={{ height: '100vh', backgroundColor: 'var(--gray-1)', overflow: 'auto' }}>
                <Box style={{ padding: '1.5rem 2rem', borderBottom: '1px solid var(--gray-4)', backgroundColor: 'white' }}>
                    <Flex align="center" gap="3">
                        <PersonIcon width="24" height="24" />
                        <Box>
                            <Heading size="7" style={{ color: 'var(--gray-12)' }}>User Profile</Heading>
                            <Text as="p" size="3" style={{ color: 'var(--gray-10)', marginTop: '0.25rem' }}>
                                Manage your account information
                            </Text>
                        </Box>
                    </Flex>
                </Box>

                <Box style={{ padding: '2rem', maxWidth: '800px', margin: '0 auto' }}>
                    {error && (
                        <Callout.Root color="red" mb="4">
                            <Callout.Icon><InfoCircledIcon /></Callout.Icon>
                            <Callout.Text>{error}</Callout.Text>
                        </Callout.Root>
                    )}
                    
                    {success && (
                        <Callout.Root color="green" mb="4">
                            <Callout.Icon><InfoCircledIcon /></Callout.Icon>
                            <Callout.Text>{success}</Callout.Text>
                        </Callout.Root>
                    )}

                    {isLoading ? (
                        <Card>
                            <Text>Loading profile...</Text>
                        </Card>
                    ) : profile && (
                        <>
                            <Card mb="4">
                                <Heading size="5" mb="4">Account Information</Heading>
                                
                                <Flex direction="column" gap="3">
                                    <Box>
                                        <Text size="2" weight="bold" color="gray">Email</Text>
                                        <Text size="3">{profile.email}</Text>
                                    </Box>
                                    
                                    <Box>
                                        <Text size="2" weight="bold" color="gray">Role</Text>
                                        <Text size="3">{profile.role === 'admin' ? 'Administrator' : 'User'}</Text>
                                    </Box>
                                    
                                    <Box>
                                        <Text size="2" weight="bold" color="gray">Member Since</Text>
                                        <Text size="3">{new Date(profile.created_at).toLocaleDateString()}</Text>
                                    </Box>
                                    
                                    {profile.last_login && (
                                        <Box>
                                            <Text size="2" weight="bold" color="gray">Last Login</Text>
                                            <Text size="3">{new Date(profile.last_login).toLocaleString()}</Text>
                                        </Box>
                                    )}
                                </Flex>
                            </Card>

                            <Card>
                                <Flex justify="between" align="center" mb="4">
                                    <Heading size="5">Personal Information</Heading>
                                    {!isEditing && (
                                        <Button onClick={() => setIsEditing(true)}>Edit Profile</Button>
                                    )}
                                </Flex>
                                
                                <Flex direction="column" gap="4">
                                    <Flex gap="4">
                                        <Box style={{ flex: 1 }}>
                                            <Text size="2" weight="bold" color="gray" mb="1">First Name</Text>
                                            {isEditing ? (
                                                <TextField.Root
                                                    value={formData.first_name}
                                                    onChange={(e) => setFormData({ ...formData, first_name: e.target.value })}
                                                    placeholder="Enter first name"
                                                />
                                            ) : (
                                                <Text size="3">{profile.first_name || '-'}</Text>
                                            )}
                                        </Box>
                                        
                                        <Box style={{ flex: 1 }}>
                                            <Text size="2" weight="bold" color="gray" mb="1">Last Name</Text>
                                            {isEditing ? (
                                                <TextField.Root
                                                    value={formData.last_name}
                                                    onChange={(e) => setFormData({ ...formData, last_name: e.target.value })}
                                                    placeholder="Enter last name"
                                                />
                                            ) : (
                                                <Text size="3">{profile.last_name || '-'}</Text>
                                            )}
                                        </Box>
                                    </Flex>
                                    
                                    <Box>
                                        <Text size="2" weight="bold" color="gray" mb="1">Company</Text>
                                        {isEditing ? (
                                            <TextField.Root
                                                value={formData.company}
                                                onChange={(e) => setFormData({ ...formData, company: e.target.value })}
                                                placeholder="Enter company name"
                                            />
                                        ) : (
                                            <Text size="3">{profile.company || '-'}</Text>
                                        )}
                                    </Box>
                                    
                                    <Box>
                                        <Text size="2" weight="bold" color="gray" mb="1">Website</Text>
                                        {isEditing ? (
                                            <TextField.Root
                                                value={formData.website_url}
                                                onChange={(e) => setFormData({ ...formData, website_url: e.target.value })}
                                                placeholder="https://example.com"
                                            />
                                        ) : (
                                            profile.website_url ? (
                                                <a href={profile.website_url} target="_blank" rel="noopener noreferrer" style={{ color: 'var(--blue-9)' }}>
                                                    {profile.website_url}
                                                </a>
                                            ) : (
                                                <Text size="3">-</Text>
                                            )
                                        )}
                                    </Box>
                                    
                                    {isEditing && (
                                        <Flex gap="3" mt="3">
                                            <Button onClick={handleSave} disabled={isSaving}>
                                                {isSaving ? 'Saving...' : 'Save Changes'}
                                            </Button>
                                            <Button variant="soft" onClick={handleCancel} disabled={isSaving}>
                                                Cancel
                                            </Button>
                                        </Flex>
                                    )}
                                </Flex>
                            </Card>
                        </>
                    )}
                </Box>
            </Box>
        </MainLayout>
    );
};

export default ProfilePage; 