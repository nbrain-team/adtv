import { useState, useEffect } from 'react';
import { Box, Flex, Heading, Text, Card, Table, Checkbox, Button, TextField, Badge, Callout, IconButton } from '@radix-ui/themes';
import { InfoCircledIcon, MagnifyingGlassIcon, PersonIcon, GearIcon } from '@radix-ui/react-icons';
import { MainLayout } from '../components/MainLayout';
import api from '../api';

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

const UserManagementPage = () => {
    const [users, setUsers] = useState<User[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState('');
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState<string | null>(null);
    const [savingUserId, setSavingUserId] = useState<string | null>(null);

    useEffect(() => {
        fetchUsers();
    }, []);

    const fetchUsers = async () => {
        try {
            const response = await api.get('/user/users');
            setUsers(response.data);
        } catch (err: any) {
            if (err.response?.status === 403) {
                setError('You do not have permission to view this page');
            } else {
                setError('Failed to load users');
            }
        } finally {
            setIsLoading(false);
        }
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
            
            // Update local state
            setUsers(users.map(u => 
                u.id === userId 
                    ? { ...u, permissions: newPermissions }
                    : u
            ));
            
            setSuccess('Permissions updated successfully');
        } catch (err) {
            setError('Failed to update permissions');
            // Revert the change
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
            
            // Update local state
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
            
            // Update local state
            setUsers(users.map(u => 
                u.id === userId 
                    ? { ...u, is_active: !u.is_active }
                    : u
            ));
            
            const user = users.find(u => u.id === userId);
            setSuccess(`User ${user?.is_active ? 'deactivated' : 'activated'} successfully`);
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Failed to update user status');
            await fetchUsers();
        } finally {
            setSavingUserId(null);
        }
    };

    const filteredUsers = users.filter(user => {
        const searchLower = searchTerm.toLowerCase();
        return (
            user.email.toLowerCase().includes(searchLower) ||
            (user.first_name?.toLowerCase() || '').includes(searchLower) ||
            (user.last_name?.toLowerCase() || '').includes(searchLower) ||
            (user.company?.toLowerCase() || '').includes(searchLower)
        );
    });

    const formatName = (user: User) => {
        if (user.first_name || user.last_name) {
            return `${user.first_name || ''} ${user.last_name || ''}`.trim();
        }
        return '-';
    };

    return (
        <MainLayout onNewChat={() => {}}>
            <Box style={{ height: '100vh', backgroundColor: 'var(--gray-1)', overflow: 'auto' }}>
                <Box style={{ padding: '1.5rem 2rem', borderBottom: '1px solid var(--gray-4)', backgroundColor: 'white' }}>
                    <Flex align="center" gap="3">
                        <GearIcon width="24" height="24" />
                        <Box>
                            <Heading size="7" style={{ color: 'var(--gray-12)' }}>User Management</Heading>
                            <Text as="p" size="3" style={{ color: 'var(--gray-10)', marginTop: '0.25rem' }}>
                                Manage user access and permissions
                            </Text>
                        </Box>
                    </Flex>
                </Box>

                <Box style={{ padding: '2rem' }}>
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

                    <Card>
                        <Flex justify="between" align="center" mb="4">
                            <Text size="3" weight="bold">
                                {filteredUsers.length} users
                            </Text>
                            
                            <Flex align="center" gap="2" style={{ maxWidth: '300px' }}>
                                <MagnifyingGlassIcon />
                                <TextField.Root
                                    placeholder="Search users..."
                                    value={searchTerm}
                                    onChange={(e) => setSearchTerm(e.target.value)}
                                />
                            </Flex>
                        </Flex>

                        {isLoading ? (
                            <Text>Loading users...</Text>
                        ) : (
                            <Box style={{ overflowX: 'auto' }}>
                                <Table.Root>
                                    <Table.Header>
                                        <Table.Row>
                                            <Table.ColumnHeaderCell>Name</Table.ColumnHeaderCell>
                                            <Table.ColumnHeaderCell>Email</Table.ColumnHeaderCell>
                                            <Table.ColumnHeaderCell>Company</Table.ColumnHeaderCell>
                                            <Table.ColumnHeaderCell>Member Since</Table.ColumnHeaderCell>
                                            <Table.ColumnHeaderCell>Last Login</Table.ColumnHeaderCell>
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
                                                <Table.Cell>{formatName(user)}</Table.Cell>
                                                <Table.Cell>{user.email}</Table.Cell>
                                                <Table.Cell>{user.company || '-'}</Table.Cell>
                                                <Table.Cell>{new Date(user.created_at).toLocaleDateString()}</Table.Cell>
                                                <Table.Cell>
                                                    {user.last_login 
                                                        ? new Date(user.last_login).toLocaleDateString()
                                                        : 'Never'
                                                    }
                                                </Table.Cell>
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
                                                            disabled={savingUserId === user.id}
                                                        />
                                                    </Table.Cell>
                                                ))}
                                                <Table.Cell align="center">
                                                    <Checkbox
                                                        checked={user.role === 'admin'}
                                                        onCheckedChange={(checked) => 
                                                            handleRoleChange(user.id, !!checked)
                                                        }
                                                        disabled={savingUserId === user.id}
                                                    />
                                                </Table.Cell>
                                                <Table.Cell>
                                                    <Button
                                                        size="1"
                                                        variant="soft"
                                                        color={user.is_active ? 'red' : 'green'}
                                                        onClick={() => handleToggleActive(user.id)}
                                                        disabled={savingUserId === user.id}
                                                    >
                                                        {user.is_active ? 'Deactivate' : 'Activate'}
                                                    </Button>
                                                </Table.Cell>
                                            </Table.Row>
                                        ))}
                                    </Table.Body>
                                </Table.Root>
                            </Box>
                        )}
                    </Card>
                </Box>
            </Box>
        </MainLayout>
    );
};

export default UserManagementPage; 