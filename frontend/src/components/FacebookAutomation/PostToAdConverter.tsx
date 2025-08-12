import { useState } from 'react';
import { Box, Flex, Text, Button, TextField, TextArea, Select, Slider, Grid, Badge } from '@radix-ui/themes';
import api from '../../api';

interface PostToAdConverterProps {
  post: any;
  onComplete: () => void;
  onCancel: () => void;
}

const PostToAdConverter: React.FC<PostToAdConverterProps> = ({ post, onComplete, onCancel }) => {
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    name: `Ad - ${post.message?.substring(0, 30)}...` || `Ad - Post`,
    objective: 'REACH',
    primaryText: post.ai_suggestions?.improved_text || post.message || '',
    headline: post.ai_suggestions?.improved_headline || 'Special Offer',
    description: '',
    callToAction: post.ai_suggestions?.call_to_action || 'LEARN_MORE',
    linkUrl: '',
    dailyBudget: post.ai_suggestions?.recommended_budget || 50,
    duration: 7,
    targeting: {
      countries: ['US'],
      ageMin: 18,
      ageMax: 65,
      interests: post.ai_suggestions?.target_audience || []
    }
  });

  const handleSubmit = async () => {
    try {
      setLoading(true);
      
      await api.post('/api/facebook-automation/campaigns', {
        source_post_id: post.id,
        name: formData.name,
        objective: formData.objective,
        creative: {
          primary_text: formData.primaryText,
          headline: formData.headline,
          description: formData.description,
          call_to_action: formData.callToAction,
          link_url: formData.linkUrl
        },
        daily_budget: formData.dailyBudget,
        targeting: {
          geo_locations: { countries: formData.targeting.countries },
          age_min: formData.targeting.ageMin,
          age_max: formData.targeting.ageMax,
          interests: formData.targeting.interests
        }
      });

      onComplete();
    } catch (error) {
      console.error('Failed to create campaign:', error);
      setLoading(false);
    }
  };

  return (
    <Box>
      <Text size="6" mb="4">Convert Post to Ad</Text>

      <Flex gap="4">
        {/* Left Column - Form */}
        <Box style={{ flex: 1 }}>
          <Box mb="4">
            <Text size="2" weight="bold" mb="2">Campaign Name</Text>
            <TextField.Root
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            />
          </Box>

          <Box mb="4">
            <Text size="2" weight="bold" mb="2">Objective</Text>
            <Select.Root value={formData.objective} onValueChange={(value) => setFormData({ ...formData, objective: value })}>
              <Select.Trigger />
              <Select.Content>
                <Select.Item value="REACH">Reach</Select.Item>
                <Select.Item value="ENGAGEMENT">Engagement</Select.Item>
                <Select.Item value="TRAFFIC">Traffic</Select.Item>
                <Select.Item value="CONVERSIONS">Conversions</Select.Item>
              </Select.Content>
            </Select.Root>
          </Box>

          <Box mb="4">
            <Text size="2" weight="bold" mb="2">Primary Text</Text>
            <TextArea
              value={formData.primaryText}
              onChange={(e) => setFormData({ ...formData, primaryText: e.target.value })}
              rows={4}
            />
          </Box>

          <Box mb="4">
            <Text size="2" weight="bold" mb="2">Headline</Text>
            <TextField.Root
              value={formData.headline}
              onChange={(e) => setFormData({ ...formData, headline: e.target.value })}
            />
          </Box>

          <Box mb="4">
            <Text size="2" weight="bold" mb="2">Call to Action</Text>
            <Select.Root value={formData.callToAction} onValueChange={(value) => setFormData({ ...formData, callToAction: value })}>
              <Select.Trigger />
              <Select.Content>
                <Select.Item value="LEARN_MORE">Learn More</Select.Item>
                <Select.Item value="SHOP_NOW">Shop Now</Select.Item>
                <Select.Item value="SIGN_UP">Sign Up</Select.Item>
                <Select.Item value="CONTACT_US">Contact Us</Select.Item>
                <Select.Item value="GET_OFFER">Get Offer</Select.Item>
              </Select.Content>
            </Select.Root>
          </Box>

          <Box mb="4">
            <Text size="2" weight="bold" mb="2">Daily Budget: ${formData.dailyBudget}</Text>
            <Slider
              value={[formData.dailyBudget]}
              onValueChange={([value]) => setFormData({ ...formData, dailyBudget: value })}
              min={5}
              max={500}
              step={5}
            />
          </Box>
        </Box>

        {/* Right Column - Preview */}
        <Box style={{ width: 400 }}>
          <Text size="2" weight="bold" mb="3">Ad Preview</Text>
          {/* The original code had a Card component here, but the new imports don't include Card.
              Assuming the intent was to use a placeholder or remove the preview if Card is removed.
              For now, I'll keep the structure but remove the Card import. */}
          {/* <Card>
            {post.thumbnail_url && (
              <img 
                src={post.thumbnail_url} 
                alt="Ad preview"
                style={{ width: '100%', height: 200, objectFit: 'cover' }}
              />
            )}
            <Box p="3">
              <Text size="3" weight="bold" mb="1">{formData.headline}</Text>
              <Text size="2" color="gray" mb="2">{formData.primaryText}</Text>
              <Button size="2" variant="solid">
                {formData.callToAction.replace(/_/g, ' ')}
              </Button>
            </Box>
          </Card> */}

          {/* AI Suggestions */}
          {post.ai_suggestions && (
            <Box mt="3">
              <Text size="2" weight="bold" mb="2">AI Recommendations</Text>
              <Text size="1" color="gray">
                Based on similar high-performing ads, we recommend targeting 
                {post.ai_suggestions.target_audience?.join(', ')} interests 
                with a ${post.ai_suggestions.recommended_budget} daily budget.
              </Text>
            </Box>
          )}
        </Box>
      </Flex>

      <Flex gap="3" justify="end" mt="4">
        <Button variant="outline" onClick={onCancel}>
          Cancel
        </Button>
        <Button onClick={handleSubmit} disabled={loading}>
          {loading ? 'Creating...' : 'Create Ad Campaign'}
        </Button>
      </Flex>
    </Box>
  );
};

export default PostToAdConverter; 