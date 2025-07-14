import React, { useState, useEffect } from 'react';
import { 
  Box, Card, Flex, Text, Heading, Button, TextField, 
  Select, Table, Badge, Dialog, Tabs, Switch, Callout 
} from '@radix-ui/themes';
import { 
  PersonIcon, LockClosedIcon, TrashIcon, Pencil1Icon, 
  CheckIcon, Cross2Icon, MagnifyingGlassIcon 
} from '@radix-ui/react-icons';

interface User {
  id: string;
  email: string;
  first_name?: string;
  last_name?: string;
  company?: string;
  website_url?: string;
  role: 'user' | 'admin';
  is_active: boolean;
  permissions: Record<string, boolean>;
  created_at: string;
  last_login?: string;
}

interface Permission {
  key: string;
  label: string;
  description: string;
}

const AVAILABLE_PERMISSIONS: Permission[] = [
  { key: 'chat', label: 'Chat', description: 'Access to AI chat functionality' },
  { key: 'history', label: 'History', description: 'View conversation history' },
  { key: 'knowledge', label: 'Knowledge Base', description: 'Access knowledge base' },
  { key: 'agents', label: 'Agents', description: 'Create and manage AI agents' },
  { key: 'data-lake', label: 'Data Lake', description: 'Access data lake features' },
  { key: 'user-management', label: 'User Management', description: 'Manage users (admin only)' }
];

export const UserManagementComponent: React.FC = () => {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [roleFilter, setRoleFilter] = useState<string>('all');
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false);
  const [editForm, setEditForm] = useState<Partial<User>>({});
  const [currentUser, setCurrentUser] = useState<User | null>(null);

  // Fetch current user
  useEffect(() => {
    fetchCurrentUser();
    fetchUsers();
  }, []);

  const fetchCurrentUser = async () => {
    try {
      const response = await fetch('/api/user/profile', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      if (response.ok) {
        const data = await response.json();
        setCurrentUser(data);
      }
    } catch (error) {
      console.error('Error fetching current user:', error);
    }
  };

  const fetchUsers = async () => {
    try {
      const response = await fetch('/api/user/users', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      if (response.ok) {
        const data = await response.json();
        setUsers(data.users);
      }
    } catch (error) {
      console.error('Error fetching users:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleEditUser = (user: User) => {
    setSelectedUser(user);
    setEditForm({
      first_name: user.first_name,
      last_name: user.last_name,
      company: user.company,
      website_url: user.website_url,
      role: user.role,
      is_active: user.is_active,
      permissions: { ...user.permissions }
    });
    setIsEditDialogOpen(true);
  };

  const handleUpdateUser = async () => {
    if (!selectedUser) return;

    try {
      const response = await fetch(`/api/user/users/${selectedUser.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify(editForm)
      });

      if (response.ok) {
        await fetchUsers();
        setIsEditDialogOpen(false);
      }
    } catch (error) {
      console.error('Error updating user:', error);
    }
  };

  const handleDeleteUser = async (userId: string) => {
    if (!confirm('Are you sure you want to delete this user?')) return;

    try {
      const response = await fetch(`/api/user/users/${userId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (response.ok) {
        await fetchUsers();
      }
    } catch (error) {
      console.error('Error deleting user:', error);
    }
  };

  const filteredUsers = users.filter(user => {
    const matchesSearch = 
      user.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
      user.first_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      user.last_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      user.company?.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesRole = roleFilter === 'all' || user.role === roleFilter;
    
    return matchesSearch && matchesRole;
  });

  if (!currentUser || currentUser.role !== 'admin') {
    return (
      <Callout.Root color="red">
        <Callout.Text>
          You don't have permission to access this page.
        </Callout.Text>
      </Callout.Root>
    );
  }

  return (
    <Box>
      <Heading size="6" mb="4">User Management</Heading>
      
      {/* Search and Filters */}
      <Card mb="4">
        <Flex gap="3" align="center">
          <Box style={{ flex: 1 }}>
            <TextField.Root
              placeholder="Search users..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            >
              <TextField.Slot>
                <MagnifyingGlassIcon />
              </TextField.Slot>
            </TextField.Root>
          </Box>
          
          <Select.Root value={roleFilter} onValueChange={setRoleFilter}>
            <Select.Trigger placeholder="Filter by role" />
            <Select.Content>
              <Select.Item value="all">All Roles</Select.Item>
              <Select.Item value="user">Users</Select.Item>
              <Select.Item value="admin">Admins</Select.Item>
            </Select.Content>
          </Select.Root>
        </Flex>
      </Card>

      {/* Users Table */}
      <Card>
        <Table.Root>
          <Table.Header>
            <Table.Row>
              <Table.ColumnHeaderCell>User</Table.ColumnHeaderCell>
              <Table.ColumnHeaderCell>Company</Table.ColumnHeaderCell>
              <Table.ColumnHeaderCell>Role</Table.ColumnHeaderCell>
              <Table.ColumnHeaderCell>Status</Table.ColumnHeaderCell>
              <Table.ColumnHeaderCell>Last Login</Table.ColumnHeaderCell>
              <Table.ColumnHeaderCell>Actions</Table.ColumnHeaderCell>
            </Table.Row>
          </Table.Header>
          
          <Table.Body>
            {filteredUsers.map(user => (
              <Table.Row key={user.id}>
                <Table.Cell>
                  <Flex direction="column">
                    <Text weight="medium">
                      {user.first_name} {user.last_name}
                    </Text>
                    <Text size="1" color="gray">{user.email}</Text>
                  </Flex>
                </Table.Cell>
                
                <Table.Cell>
                  <Text>{user.company || '-'}</Text>
                </Table.Cell>
                
                <Table.Cell>
                  <Badge color={user.role === 'admin' ? 'red' : 'blue'}>
                    {user.role}
                  </Badge>
                </Table.Cell>
                
                <Table.Cell>
                  <Badge color={user.is_active ? 'green' : 'gray'}>
                    {user.is_active ? 'Active' : 'Inactive'}
                  </Badge>
                </Table.Cell>
                
                <Table.Cell>
                  <Text size="2">
                    {user.last_login 
                      ? new Date(user.last_login).toLocaleDateString()
                      : 'Never'
                    }
                  </Text>
                </Table.Cell>
                
                <Table.Cell>
                  <Flex gap="2">
                    <Button 
                      size="1" 
                      variant="soft"
                      onClick={() => handleEditUser(user)}
                      disabled={user.id === currentUser.id}
                    >
                      <Pencil1Icon />
                    </Button>
                    <Button 
                      size="1" 
                      variant="soft" 
                      color="red"
                      onClick={() => handleDeleteUser(user.id)}
                      disabled={user.id === currentUser.id}
                    >
                      <TrashIcon />
                    </Button>
                  </Flex>
                </Table.Cell>
              </Table.Row>
            ))}
          </Table.Body>
        </Table.Root>
      </Card>

      {/* Edit User Dialog */}
      <Dialog.Root open={isEditDialogOpen} onOpenChange={setIsEditDialogOpen}>
        <Dialog.Content style={{ maxWidth: 600 }}>
          <Dialog.Title>Edit User</Dialog.Title>
          
          <Tabs.Root defaultValue="profile">
            <Tabs.List>
              <Tabs.Trigger value="profile">Profile</Tabs.Trigger>
              <Tabs.Trigger value="permissions">Permissions</Tabs.Trigger>
            </Tabs.List>
            
            <Box mt="4">
              <Tabs.Content value="profile">
                <Flex direction="column" gap="3">
                  <Box>
                    <Text size="2" weight="medium" mb="1">First Name</Text>
                    <TextField.Root
                      value={editForm.first_name || ''}
                      onChange={(e) => setEditForm({
                        ...editForm,
                        first_name: e.target.value
                      })}
                    />
                  </Box>
                  
                  <Box>
                    <Text size="2" weight="medium" mb="1">Last Name</Text>
                    <TextField.Root
                      value={editForm.last_name || ''}
                      onChange={(e) => setEditForm({
                        ...editForm,
                        last_name: e.target.value
                      })}
                    />
                  </Box>
                  
                  <Box>
                    <Text size="2" weight="medium" mb="1">Company</Text>
                    <TextField.Root
                      value={editForm.company || ''}
                      onChange={(e) => setEditForm({
                        ...editForm,
                        company: e.target.value
                      })}
                    />
                  </Box>
                  
                  <Box>
                    <Text size="2" weight="medium" mb="1">Role</Text>
                    <Select.Root 
                      value={editForm.role}
                      onValueChange={(value) => setEditForm({
                        ...editForm,
                        role: value as 'user' | 'admin'
                      })}
                    >
                      <Select.Trigger />
                      <Select.Content>
                        <Select.Item value="user">User</Select.Item>
                        <Select.Item value="admin">Admin</Select.Item>
                      </Select.Content>
                    </Select.Root>
                  </Box>
                  
                  <Flex align="center" gap="2">
                    <Switch
                      checked={editForm.is_active}
                      onCheckedChange={(checked) => setEditForm({
                        ...editForm,
                        is_active: checked
                      })}
                    />
                    <Text size="2">Active</Text>
                  </Flex>
                </Flex>
              </Tabs.Content>
              
              <Tabs.Content value="permissions">
                <Flex direction="column" gap="3">
                  {AVAILABLE_PERMISSIONS.map(permission => (
                    <Card key={permission.key}>
                      <Flex justify="between" align="center">
                        <Box>
                          <Text weight="medium">{permission.label}</Text>
                          <Text size="1" color="gray">
                            {permission.description}
                          </Text>
                        </Box>
                        <Switch
                          checked={editForm.permissions?.[permission.key] || false}
                          onCheckedChange={(checked) => setEditForm({
                            ...editForm,
                            permissions: {
                              ...editForm.permissions,
                              [permission.key]: checked
                            }
                          })}
                          disabled={
                            permission.key === 'user-management' && 
                            editForm.role !== 'admin'
                          }
                        />
                      </Flex>
                    </Card>
                  ))}
                </Flex>
              </Tabs.Content>
            </Box>
          </Tabs.Root>
          
          <Flex gap="3" mt="4" justify="end">
            <Dialog.Close>
              <Button variant="soft" color="gray">
                Cancel
              </Button>
            </Dialog.Close>
            <Button onClick={handleUpdateUser}>
              Save Changes
            </Button>
          </Flex>
        </Dialog.Content>
      </Dialog.Root>
    </Box>
  );
}; 