import React from 'react';
import { Flex } from '@radix-ui/themes';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export const Sidebar = ({ onNewChat }: { onNewChat: () => void }) => {
    const navigate = useNavigate();
    const { userProfile } = useAuth();

    const handleNewChatClick = () => {
        navigate('/home');
        onNewChat();
    };

    const hasPermission = (module: string) => {
        // Admins always have access to campaigns
        if (module === 'campaigns' && userProfile?.role === 'admin') {
            return true;
        }
        
        const hasIt = userProfile?.permissions?.[module] === true;
        console.log(`Permission check for ${module}:`, hasIt, userProfile?.permissions);
        return hasIt;
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
                    <button className="sidebar-icon" title="Chat" onClick={handleNewChatClick}>
                        <img src="/new-icons/13.png" alt="Chat" />
                    </button>
                )}
                {hasPermission('agents') && (
                    <button className="sidebar-icon" title="Agent Ideator" onClick={() => navigate('/agents')}>
                        <img src="/new-icons/3.png" alt="Agent Ideator" />
                    </button>
                )}
            </Flex>
            
            <Flex direction="column" align="center" gap="8" style={{ marginBottom: '1rem' }}>
                <button className="sidebar-icon" title="Profile" onClick={() => navigate('/profile')}>
                    <img src="/new-icons/16.png" alt="Profile" />
                </button>
            </Flex>
        </Flex>
    );
}; 