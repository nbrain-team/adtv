import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Button, Card, Flex, Heading, Text, TextField } from '@radix-ui/themes';
import api from '../api';

const LoginPage = () => {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const { login } = useAuth();
    const navigate = useNavigate();

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        try {
            // The backend expects form data for the login endpoint
            const params = new URLSearchParams();
            params.append('username', email);
            params.append('password', password);

            const response = await api.post('/login', params, {
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            });

            if (response.data.access_token) {
                login(response.data.access_token);
                navigate('/landing');
            }
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Failed to login. Please check your credentials.');
        }
    };

    return (
        <Flex direction="column" align="center" justify="center" gap="5" style={{ height: '100vh', backgroundColor: 'var(--gray-2)' }}>
            <img src="/new-icons/adtv-logo.png" alt="ADTV Logo" style={{ maxWidth: '250px' }} />
            <Card style={{ width: 400, padding: '2rem' }}>
                <Heading align="center" mb="5">Login</Heading>
                <form onSubmit={handleSubmit}>
                    <Flex direction="column" gap="4">
                        <TextField.Root
                            placeholder="Email"
                            type="email"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            required
                        />
                        <TextField.Root
                            placeholder="Password"
                            type="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            required
                        />
                        {error && <Text color="red" size="2">{error}</Text>}
                        <Button type="submit">Log In</Button>
                    </Flex>
                </form>
                <Flex mt="4" justify="center">
                    <Text size="2">
                        Don't have an account? <Link to="/signup">Sign up</Link>
                    </Text>
                </Flex>
            </Card>
        </Flex>
    );
};

export default LoginPage; 