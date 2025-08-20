import { Box, Heading, Text, Card } from '@radix-ui/themes';
import { MainLayout } from '../components/MainLayout';
import { useNavigate } from 'react-router-dom';

export const PrivacyPage = () => {
  const navigate = useNavigate();
  return (
    <MainLayout onNewChat={() => navigate('/home')}>
      <Box p="5" style={{ maxWidth: 900, margin: '0 auto' }}>
        <Heading size="7" mb="4">Privacy Policy</Heading>
        <Card>
          <Box p="5">
            <Text as="p" mb="3">Effective date: {new Date().toISOString().slice(0,10)}</Text>
            <Text as="p" mb="3">We collect and process Facebook Page content you authorize (page ID, name, posts and metadata) to power the ADTV platform features like post review and ad creation. We do not sell personal data.</Text>
            <Text as="p" mb="3">Data we collect: page identifiers, post content/URLs, engagement metrics, and access tokens required to operate the integration. We use this only to provide the service and store it securely. Access is limited to authorized personnel.</Text>
            <Text as="p" mb="3">Retention: we retain data while your account is active or as needed to provide the service and to meet legal obligations. You may request deletion at any time (see Data Deletion).</Text>
            <Text as="p" mb="3">Your rights: request access, correction, or deletion by contacting support at privacy@adtvmedia.com.</Text>
          </Box>
        </Card>
      </Box>
    </MainLayout>
  );
};

export const TermsPage = () => {
  const navigate = useNavigate();
  return (
    <MainLayout onNewChat={() => navigate('/home')}>
      <Box p="5" style={{ maxWidth: 900, margin: '0 auto' }}>
        <Heading size="7" mb="4">Terms of Service</Heading>
        <Card>
          <Box p="5">
            <Text as="p" mb="3">By using ADTV, you agree to comply with applicable laws and Facebook’s platform policies. You are responsible for ensuring you have rights to Page content you connect.</Text>
            <Text as="p" mb="3">We provide the service "as is" without warranties. Liability is limited to the extent permitted by law.</Text>
          </Box>
        </Card>
      </Box>
    </MainLayout>
  );
};

export const DataDeletionPage = () => {
  const navigate = useNavigate();
  return (
    <MainLayout onNewChat={() => navigate('/home')}>
      <Box p="5" style={{ maxWidth: 900, margin: '0 auto' }}>
        <Heading size="7" mb="4">Data Deletion Instructions</Heading>
        <Card>
          <Box p="5">
            <Text as="p" mb="3">To request deletion of your data and tokens, email deletion@adtvmedia.com from your account email. We will confirm and complete deletion within 30 days.</Text>
            <Text as="p">Alternatively, contact support via your account dashboard and reference “Data Deletion”.</Text>
          </Box>
        </Card>
      </Box>
    </MainLayout>
  );
};

export default PrivacyPage;


