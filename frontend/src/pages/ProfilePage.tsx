import { useState, useEffect } from 'react';
import { Box, Flex, Heading, Text, Card, TextField, Button, Callout, Table, Checkbox, Badge, IconButton } from '@radix-ui/themes';
import { InfoCircledIcon, PersonIcon, ExitIcon, MagnifyingGlassIcon, GearIcon } from '@radix-ui/react-icons';
import { MainLayout } from '../components/MainLayout';
import api from '../api';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';

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

interface User {
    id: string;
    email: string;
    first_name: string | null;
    last_name: string | null;
    company: string | null;
    role: string;
    permissions: Record<string, boolean>;
    created_at: string;
    last_login: string | null;
    is_active: boolean;
}

const MODULES = [
    { key: 'chat', name: 'Chat' },
    { key: 'history', name: 'History' },
    { key: 'knowledge', name: 'Knowledge Base' },
    { key: 'agents', name: 'Agents' },
    { key: 'data-lake', name: 'Data Lake' },
];

const ProfilePage = () => {
    const [profile, setProfile] = useState<UserProfile | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [isSaving, setIsSaving] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState<string | null>(null);
    const { logout } = useAuth();
    const navigate = useNavigate();
    
    // Form fields
    const [firstName, setFirstName] = useState('');
    const [lastName, setLastName] = useState('');
    const [company, setCompany] = useState('');
    const [websiteUrl, setWebsiteUrl] = useState('');
    
    // Admin-only state for user management
    const [users, setUsers] = useState<User[]>([]);
    const [searchTerm, setSearchTerm] = useState('');
    const [savingUserId, setSavingUserId] = useState<string | null>(null);

    useEffect(() => {
        fetchProfile();
    }, []);

    useEffect(() => {
        if (profile?.role === 'admin') {
            fetchUsers();
        }
    }, [profile]);

    const fetchProfile = async () => {
        try {
            const response = await api.get('/user/profile');
            setProfile(response.data);
            setFirstName(response.data.first_name || '');
            setLastName(response.data.last_name || '');
            setCompany(response.data.company || '');
            setWebsiteUrl(response.data.website_url || '');
        } catch (err) {
            setError('Failed to load profile');
        } finally {
            setIsLoading(false);
        }
    };

    const fetchUsers = async () => {
        try {
            const response = await api.get('/user/users');
            setUsers(response.data);
        } catch (err: any) {
            console.error('Failed to load users:', err);
        }
    };

    const handleSave = async () => {
        setIsSaving(true);
        setError(null);
        setSuccess(null);
        
        try {
            await api.put('/user/profile', {
                first_name: firstName,
                last_name: lastName,
                company: company,
                website_url: websiteUrl
            });
            
            setSuccess('Profile updated successfully!');
            fetchProfile();
        } catch (err) {
            setError('Failed to update profile');
        } finally {
            setIsSaving(false);
        }
    };

    const handleLogout = () => {
        logout();
        navigate('/login');
    };

    const handlePermissionChange = async (userId: string, module: string, value: boolean) => {
        const user = users.find(u => u.id === userId);
        if (!user) return;

        const newPermissions = { ...user.permissions, [module]: value };
        
        setSavingUserId(userId);
        setError(null);
        setSuccess(null);
        
        try {
            await api.put(`/user/users/${userId}/permissions`, {
                permissions: newPermissions
            });
            
            setUsers(users.map(u => 
                u.id === userId 
                    ? { ...u, permissions: newPermissions }
                    : u
            ));
            
            setSuccess('Permissions updated successfully');
        } catch (err) {
            setError('Failed to update permissions');
            await fetchUsers();
        } finally {
            setSavingUserId(null);
        }
    };

    const handleRoleChange = async (userId: string, isAdmin: boolean) => {
        setSavingUserId(userId);
        setError(null);
        setSuccess(null);
        
        try {
            await api.put(`/user/users/${userId}/permissions`, {
                role: isAdmin ? 'admin' : 'user',
                permissions: users.find(u => u.id === userId)?.permissions
            });
            
            setUsers(users.map(u => 
                u.id === userId 
                    ? { ...u, role: isAdmin ? 'admin' : 'user' }
                    : u
            ));
            
            setSuccess('Role updated successfully');
        } catch (err) {
            setError('Failed to update role');
            await fetchUsers();
        } finally {
            setSavingUserId(null);
        }
    };

    const handleToggleActive = async (userId: string) => {
        setSavingUserId(userId);
        setError(null);
        setSuccess(null);
        
        try {
            await api.put(`/user/users/${userId}/toggle-active`);
            await fetchUsers();
            setSuccess('User status updated successfully');
        } catch (err) {
            setError('Failed to update user status');
        } finally {
            setSavingUserId(null);
        }
    };

    const filteredUsers = users.filter(user =>
        user.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
        (user.first_name?.toLowerCase() || '').includes(searchTerm.toLowerCase()) ||
        (user.last_name?.toLowerCase() || '').includes(searchTerm.toLowerCase()) ||
        (user.company?.toLowerCase() || '').includes(searchTerm.toLowerCase())
    );

    return (
        <MainLayout onNewChat={() => {}}>
            <Box style={{ height: '100vh', backgroundColor: 'var(--gray-1)', overflow: 'auto' }}>
                <Box style={{ padding: '1.5rem 2rem', borderBottom: '1px solid var(--gray-4)', backgroundColor: 'white' }}>
                    <Flex align="center" justify="between">
                        <Flex align="center" gap="3">
                            <PersonIcon width="24" height="24" />
                            <Box>
                                <Heading size="7" style={{ color: 'var(--gray-12)' }}>User Profile</Heading>
                                <Text as="p" size="3" style={{ color: 'var(--gray-10)', marginTop: '0.25rem' }}>
                                    Manage your account information{profile?.role === 'admin' && ' and user permissions'}
                                </Text>
                            </Box>
                        </Flex>
                        <Button onClick={handleLogout} variant="soft" color="red">
                            <ExitIcon />
                            Logout
                        </Button>
                    </Flex>
                </Box>

                <Box style={{ padding: '2rem', maxWidth: '1200px', margin: '0 auto' }}>
                    {error && (
                        <Callout.Root color="red" mb="4">
                            <Callout.Icon>
                                <InfoCircledIcon />
                            </Callout.Icon>
                            <Callout.Text>{error}</Callout.Text>
                        </Callout.Root>
                    )}
                    
                    {success && (
                        <Callout.Root color="green" mb="4">
                            <Callout.Icon>
                                <InfoCircledIcon />
                            </Callout.Icon>
                            <Callout.Text>{success}</Callout.Text>
                        </Callout.Root>
                    )}

                    {isLoading ? (
                        <Text>Loading profile...</Text>
                    ) : profile && (
                        <>
                            <Card mb="4">
                                <Heading size="5" mb="4">Account Information</Heading>
                                
                                <Flex direction="column" gap="3">
                                    <Box>
                                        <Text size="3">
                                            <Text as="span" weight="bold">Email:</Text> {profile.email}
                                        </Text>
                                    </Box>
                                    
                                    <Box>
                                        <Text size="3">
                                            <Text as="span" weight="bold">Role:</Text> {profile.role === 'admin' ? 'Administrator' : 'User'}
                                        </Text>
                                    </Box>
                                    
                                    <Box>
                                        <Text size="3">
                                            <Text as="span" weight="bold">Member Since:</Text> {new Date(profile.created_at).toLocaleDateString()}
                                        </Text>
                                    </Box>
                                    
                                    {profile.last_login && (
                                        <Box>
                                            <Text size="3">
                                                <Text as="span" weight="bold">Last Login:</Text> {new Date(profile.last_login).toLocaleString()}
                                            </Text>
                                        </Box>
                                    )}
                                </Flex>
                            </Card>

                            <Card mb="4">
                                <Heading size="5" mb="4">Profile Details</Heading>
                                
                                <Flex direction="column" gap="4">
                                    <Flex gap="4">
                                        <Box style={{ flex: 1 }}>
                                            <Text as="label" size="2" mb="1" weight="medium">
                                                First Name
                                            </Text>
                                            <TextField.Root
                                                value={firstName}
                                                onChange={(e) => setFirstName(e.target.value)}
                                                placeholder="Enter your first name"
                                            />
                                        </Box>
                                        
                                        <Box style={{ flex: 1 }}>
                                            <Text as="label" size="2" mb="1" weight="medium">
                                                Last Name
                                            </Text>
                                            <TextField.Root
                                                value={lastName}
                                                onChange={(e) => setLastName(e.target.value)}
                                                placeholder="Enter your last name"
                                            />
                                        </Box>
                                    </Flex>
                                    
                                    <Box>
                                        <Text as="label" size="2" mb="1" weight="medium">
                                            Company
                                        </Text>
                                        <TextField.Root
                                            value={company}
                                            onChange={(e) => setCompany(e.target.value)}
                                            placeholder="Enter your company name"
                                        />
                                    </Box>
                                    
                                    <Box>
                                        <Text as="label" size="2" mb="1" weight="medium">
                                            Website
                                        </Text>
                                        <TextField.Root
                                            value={websiteUrl}
                                            onChange={(e) => setWebsiteUrl(e.target.value)}
                                            placeholder="https://example.com"
                                        />
                                    </Box>
                                    
                                    <Flex gap="3" mt="2">
                                        <Button onClick={handleSave} disabled={isSaving}>
                                            {isSaving ? 'Saving...' : 'Save Changes'}
                                        </Button>
                                        <Button 
                                            variant="soft" 
                                            onClick={() => {
                                                setFirstName(profile.first_name || '');
                                                setLastName(profile.last_name || '');
                                                setCompany(profile.company || '');
                                                setWebsiteUrl(profile.website_url || '');
                                            }}
                                        >
                                            Reset
                                        </Button>
                                    </Flex>
                                </Flex>
                            </Card>

                            {/* Admin-only User Management Section */}
                            {profile.role === 'admin' && (
                                <Card>
                                    <Flex align="center" justify="between" mb="4">
                                        <Flex align="center" gap="2">
                                            <GearIcon width="20" height="20" />
                                            <Heading size="5">User Management</Heading>
                                        </Flex>
                                        <TextField.Root
                                            placeholder="Search users..."
                                            value={searchTerm}
                                            onChange={(e) => setSearchTerm(e.target.value)}
                                            style={{ maxWidth: '300px' }}
                                        >
                                            <TextField.Slot>
                                                <MagnifyingGlassIcon height="16" width="16" />
                                            </TextField.Slot>
                                        </TextField.Root>
                                    </Flex>

                                    <Box style={{ overflowX: 'auto' }}>
                                        <Table.Root>
                                            <Table.Header>
                                                <Table.Row>
                                                    <Table.ColumnHeaderCell>Name</Table.ColumnHeaderCell>
                                                    <Table.ColumnHeaderCell>Email</Table.ColumnHeaderCell>
                                                    <Table.ColumnHeaderCell>Company</Table.ColumnHeaderCell>
                                                    <Table.ColumnHeaderCell>Status</Table.ColumnHeaderCell>
                                                    {MODULES.map(module => (
                                                        <Table.ColumnHeaderCell key={module.key} align="center">
                                                            {module.name}
                                                        </Table.ColumnHeaderCell>
                                                    ))}
                                                    <Table.ColumnHeaderCell align="center">Admin</Table.ColumnHeaderCell>
                                                    <Table.ColumnHeaderCell>Actions</Table.ColumnHeaderCell>
                                                </Table.Row>
                                            </Table.Header>
                                            <Table.Body>
                                                {filteredUsers.map(user => (
                                                    <Table.Row key={user.id}>
                                                        <Table.Cell>
                                                            {user.first_name || user.last_name 
                                                                ? `${user.first_name || ''} ${user.last_name || ''}`.trim()
                                                                : '-'
                                                            }
                                                        </Table.Cell>
                                                        <Table.Cell>{user.email}</Table.Cell>
                                                        <Table.Cell>{user.company || '-'}</Table.Cell>
                                                        <Table.Cell>
                                                            <Badge color={user.is_active ? 'green' : 'red'}>
                                                                {user.is_active ? 'Active' : 'Inactive'}
                                                            </Badge>
                                                        </Table.Cell>
                                                        {MODULES.map(module => (
                                                            <Table.Cell key={module.key} align="center">
                                                                <Checkbox
                                                                    checked={user.permissions[module.key] || false}
                                                                    onCheckedChange={(checked) => 
                                                                        handlePermissionChange(user.id, module.key, !!checked)
                                                                    }
                                                                    disabled={savingUserId === user.id || user.id === profile.id}
                                                                />
                                                            </Table.Cell>
                                                        ))}
                                                        <Table.Cell align="center">
                                                            <Checkbox
                                                                checked={user.role === 'admin'}
                                                                onCheckedChange={(checked) => 
                                                                    handleRoleChange(user.id, !!checked)
                                                                }
                                                                disabled={savingUserId === user.id || user.id === profile.id}
                                                            />
                                                        </Table.Cell>
                                                        <Table.Cell>
                                                            <Button
                                                                size="1"
                                                                variant="soft"
                                                                color={user.is_active ? 'red' : 'green'}
                                                                onClick={() => handleToggleActive(user.id)}
                                                                disabled={savingUserId === user.id || user.id === profile.id}
                                                            >
                                                                {user.is_active ? 'Deactivate' : 'Activate'}
                                                            </Button>
                                                        </Table.Cell>
                                                    </Table.Row>
                                                ))}
                                            </Table.Body>
                                        </Table.Root>
                                    </Box>
                                </Card>
                            )}
                        </>
                    )}
                </Box>
            </Box>
        </MainLayout>
    );
};

export default ProfilePage; 