import { Flex } from '@radix-ui/themes';
import { useNavigate } from 'react-router-dom';
import { useState, useEffect } from 'react';
import api from '../api';

interface UserProfile {
    role: string;
    permissions: Record<string, boolean>;
}

export const Sidebar = ({ onNewChat }: { onNewChat: () => void }) => {
    const navigate = useNavigate();
    const [userProfile, setUserProfile] = useState<UserProfile | null>(null);

    useEffect(() => {
        // Fetch user profile to check permissions
        api.get('/user/profile')
            .then(response => setUserProfile(response.data))
            .catch(() => {});
    }, []);

    const handleNewChatClick = () => {
        navigate('/');
        onNewChat();
    };

    const hasPermission = (module: string) => {
        return userProfile?.permissions?.[module] !== false;
    };

    const isAdmin = () => {
        return userProfile?.role === 'admin';
    };

    return (
        <Flex 
            direction="column" 
            align="center" 
            gap="4"
            style={{ 
                width: 'var(--sidebar-width)', 
                height: '100vh', 
                padding: '1.5rem 0',
                backgroundColor: 'var(--sidebar-bg)',
                borderRight: '1px solid var(--border)',
                boxShadow: 'var(--shadow)',
                position: 'fixed',
                left: 0,
                top: 0,
                zIndex: 100
            }}
        >
            <button className="sidebar-icon" title="Home" onClick={() => navigate('/home')} style={{ background: 'none', border: 'none', padding: 0, cursor: 'pointer' }}>
                <img src="/new-icons/1.png" alt="ADTV Logo" style={{ width: '60px', height: '60px', marginBottom: '1rem' }} />
            </button>
            
            <Flex direction="column" align="center" gap="8" style={{ marginTop: '125px', flex: 1 }}>
                {hasPermission('chat') && (
                    <button className="sidebar-icon" title="New Chat" onClick={handleNewChatClick}>
                        <img src="/new-icons/13.png" alt="New Chat" />
                    </button>
                )}
                {hasPermission('history') && (
                    <button className="sidebar-icon" title="Chat History" onClick={() => navigate('/history')}>
                        <img src="/new-icons/2.png" alt="History" />
                    </button>
                )}
                {hasPermission('knowledge') && (
                    <button className="sidebar-icon" title="Knowledge Base" onClick={() => navigate('/knowledge')}>
                        <img src="/new-icons/4.png" alt="Upload" />
                    </button>
                )}
                {hasPermission('agents') && (
                    <button className="sidebar-icon" title="Automation Agents" onClick={() => navigate('/agents')}>
                        <img src="/new-icons/3.png" alt="Automation Agents" />
                    </button>
                )}
                {hasPermission('data-lake') && (
                    <button className="sidebar-icon" title="Data Lake" onClick={() => navigate('/data-lake')}>
                        <img src="/new-icons/14.png" alt="Data Lake" />
                    </button>
                )}
                {isAdmin() && (
                    <button className="sidebar-icon" title="User Management" onClick={() => navigate('/user-management')}>
                        <img src="/new-icons/15.png" alt="User Management" />
                    </button>
                )}
            </Flex>
            
            <button className="sidebar-icon" title="Profile" onClick={() => navigate('/profile')} style={{ marginBottom: '1rem' }}>
                <img src="/new-icons/16.png" alt="Profile" />
            </button>
        </Flex>
    );
}; 