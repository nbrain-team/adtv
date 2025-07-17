import React, { useState, useEffect } from 'react';
import { Box, Flex, Text, TextArea, Button, Heading, Checkbox, TextField } from '@radix-ui/themes';
import { CalendarIcon, ImageIcon } from '@radix-ui/react-icons';
import { Client, SocialPost, PostFormData, Platform } from './types';
import { api } from '../../services/api';

interface PostModalProps {
  client: Client;
  post: SocialPost | null;
  onSave: () => void;
  onCancel: () => void;
}

export const PostModal: React.FC<PostModalProps> = ({
  client,
  post,
  onSave,
  onCancel
}) => {
  const [formData, setFormData] = useState<PostFormData>({
    content: '',
    platforms: [Platform.FACEBOOK],
    scheduled_time: new Date().toISOString().slice(0, 16),
    media_urls: []
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (post) {
      setFormData({
        content: post.content,
        platforms: post.platforms,
        scheduled_time: new Date(post.scheduled_time).toISOString().slice(0, 16),
        media_urls: post.media_urls || [],
        video_clip_id: post.video_clip?.id
      });
    }
  }, [post]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const payload = {
        ...formData,
        scheduled_time: new Date(formData.scheduled_time).toISOString()
      };

      if (post) {
        await api.put(`/api/ad-traffic/posts/${post.id}`, payload);
      } else {
        await api.post(`/api/ad-traffic/clients/${client.id}/posts`, payload);
      }
      onSave();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to save post');
    } finally {
      setLoading(false);
    }
  };

  const togglePlatform = (platform: Platform) => {
    const platforms = formData.platforms.includes(platform)
      ? formData.platforms.filter(p => p !== platform)
      : [...formData.platforms, platform];
    
    setFormData({ ...formData, platforms });
  };

  const platformConfig = [
    { value: Platform.FACEBOOK, label: 'Facebook', color: '#1877f2' },
    { value: Platform.INSTAGRAM, label: 'Instagram', color: '#E4405F' },
    { value: Platform.TIKTOK, label: 'TikTok', color: '#000000' }
  ];

  return (
    <Box>
      <Heading size="5" mb="4">
        {post ? 'Edit Post' : 'Create New Post'}
      </Heading>

      <form onSubmit={handleSubmit}>
        <Flex direction="column" gap="4">
          <Box>
            <Text as="label" size="2" weight="medium">Platforms *</Text>
            <Flex gap="3" mt="2">
              {platformConfig.map(platform => (
                <label key={platform.value} style={{ cursor: 'pointer' }}>
                  <Flex align="center" gap="2">
                    <Checkbox
                      checked={formData.platforms.includes(platform.value)}
                      onCheckedChange={() => togglePlatform(platform.value)}
                    />
                    <Text size="2" style={{ color: platform.color }}>
                      {platform.label}
                    </Text>
                  </Flex>
                </label>
              ))}
            </Flex>
          </Box>

          <Box>
            <Text as="label" size="2" weight="medium" htmlFor="content">Content *</Text>
            <TextArea
              id="content"
              value={formData.content}
              onChange={(e) => setFormData({ ...formData, content: e.target.value })}
              placeholder="What's on your mind?"
              rows={6}
              required
              style={{ marginTop: '0.5rem' }}
            />
            <Text size="1" color="gray" style={{ marginTop: '0.25rem' }}>
              {formData.content.length} characters
            </Text>
          </Box>

          <Box>
            <Text as="label" size="2" weight="medium" htmlFor="scheduled_time">
              <CalendarIcon style={{ display: 'inline', marginRight: '0.25rem' }} />
              Schedule Time *
            </Text>
            <TextField.Root
              id="scheduled_time"
              type="datetime-local"
              value={formData.scheduled_time}
              onChange={(e) => setFormData({ ...formData, scheduled_time: e.target.value })}
              required
              style={{ marginTop: '0.5rem' }}
            />
          </Box>

          <Box>
            <Text as="label" size="2" weight="medium">
              <ImageIcon style={{ display: 'inline', marginRight: '0.25rem' }} />
              Media URLs
            </Text>
            <TextArea
              value={formData.media_urls?.join('\n') || ''}
              onChange={(e) => setFormData({ 
                ...formData, 
                media_urls: e.target.value.split('\n').filter(url => url.trim()) 
              })}
              placeholder="Enter image/video URLs, one per line"
              rows={3}
              style={{ marginTop: '0.5rem' }}
            />
          </Box>

          {post?.video_clip && (
            <Box>
              <Text size="2" weight="medium">Attached Video Clip</Text>
              <Box style={{ 
                padding: '0.5rem', 
                backgroundColor: 'var(--gray-2)', 
                borderRadius: '4px',
                marginTop: '0.5rem'
              }}>
                <Text size="2">{post.video_clip.title}</Text>
                <Text size="1" color="gray">
                  {Math.round(post.video_clip.duration)}s • {post.video_clip.content_type}
                </Text>
              </Box>
            </Box>
          )}

          {error && (
            <Text size="2" color="red">{error}</Text>
          )}

          <Flex gap="3" justify="end">
            <Button 
              type="button" 
              variant="soft" 
              onClick={onCancel}
              disabled={loading}
            >
              Cancel
            </Button>
            <Button 
              type="submit" 
              disabled={loading || !formData.content || formData.platforms.length === 0}
            >
              {loading ? 'Saving...' : (post ? 'Update' : 'Create')} Post
            </Button>
          </Flex>
        </Flex>
      </form>
    </Box>
  );
}; 