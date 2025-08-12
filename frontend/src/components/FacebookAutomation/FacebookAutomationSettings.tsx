import { useState, useEffect } from 'react';
import { Box, Flex, Text, Card, Button, Slider, Switch, TextField } from '@radix-ui/themes';
import api from '../../api';

interface ClientSettings {
  is_active: boolean;
  auto_convert_posts: boolean;
  default_daily_budget: number;
  default_campaign_duration: number;
  automation_rules: {
    min_text_length: number;
    require_image: boolean;
    auto_approve: boolean;
    target_audience: string;
    optimization_goal: string;
  };
}

interface FacebookAutomationSettingsProps {
  clientId: string | null;
  onUpdate: () => void;
}

const FacebookAutomationSettings: React.FC<FacebookAutomationSettingsProps> = ({ clientId, onUpdate }) => {
  const [settings, setSettings] = useState<ClientSettings | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (clientId) {
      fetchSettings();
    }
  }, [clientId]);

  const fetchSettings = async () => {
    try {
      setLoading(true);
      const response = await api.get(`/facebook-automation/clients/${clientId}`);
      setSettings({
        is_active: response.data.is_active,
        auto_convert_posts: response.data.auto_convert_posts,
        default_daily_budget: response.data.default_daily_budget,
        default_campaign_duration: response.data.default_campaign_duration,
        automation_rules: response.data.automation_rules
      });
    } catch (error) {
      console.error('Failed to fetch settings:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    if (!settings) return;

    try {
      setSaving(true);
      await api.put(`/facebook-automation/clients/${clientId}`, settings);
      onUpdate();
    } catch (error) {
      console.error('Failed to save settings:', error);
    } finally {
      setSaving(false);
    }
  };

  if (loading || !settings) {
    return (
      <Card>
        <Box p="6">
          <Text>Loading settings...</Text>
        </Box>
      </Card>
    );
  }

  return (
    <Box>
      {/* General Settings */}
      <Card mb="4">
        <Box p="4">
          <Text size="3" weight="bold" mb="2">Account Active</Text>
          <Switch
            checked={settings.is_active}
            onCheckedChange={(checked) => setSettings({ ...settings, is_active: checked })}
          />

          <Text size="3" weight="bold" mb="2">Auto Convert Posts</Text>
          <Switch
            checked={settings.auto_convert_posts}
            onCheckedChange={(checked) => setSettings({ ...settings, auto_convert_posts: checked })}
          />

          <Text size="3" weight="bold" mb="2">Default Daily Budget</Text>
          <TextField.Root
            type="number"
            value={settings.default_daily_budget.toString()}
            onChange={(e) => setSettings({ 
              ...settings, 
              default_daily_budget: parseFloat(e.target.value) || 0 
            })}
          />

          <Text size="3" weight="bold" mb="2">Default Campaign Duration (days)</Text>
          <TextField.Root
            type="number"
            value={settings.default_campaign_duration.toString()}
            onChange={(e) => setSettings({ 
              ...settings, 
              default_campaign_duration: parseInt(e.target.value) || 7 
            })}
          />
        </Box>
      </Card>

      {/* Automation Rules */}
      <Card mb="4">
        <Box p="4">
          <Text size="3" weight="bold" mb="2">Minimum Text Length</Text>
          <TextField.Root
            type="number"
            value={settings.automation_rules.min_text_length.toString()}
            onChange={(e) => setSettings({ 
              ...settings, 
              automation_rules: {
                ...settings.automation_rules,
                min_text_length: parseInt(e.target.value) || 50
              }
            })}
          />
          <Text size="1" color="gray" mt="1">Posts shorter than this won't be auto-converted</Text>

          <Text size="3" weight="bold" mb="2">Require Image</Text>
          <Switch
            checked={settings.automation_rules.require_image}
            onCheckedChange={(checked) => setSettings({ 
              ...settings, 
              automation_rules: {
                ...settings.automation_rules,
                require_image: checked
              }
            })}
          />

          <Text size="3" weight="bold" mb="2">Auto Approve</Text>
          <Switch
            checked={settings.automation_rules.auto_approve}
            onCheckedChange={(checked) => setSettings({ 
              ...settings, 
              automation_rules: {
                ...settings.automation_rules,
                auto_approve: checked
              }
            })}
          />
        </Box>
      </Card>

      {/* Save Button */}
      <Flex justify="end">
        <Button onClick={handleSave} disabled={saving}>
          {saving ? 'Saving...' : 'Save Settings'}
        </Button>
      </Flex>
    </Box>
  );
};

export default FacebookAutomationSettings; 