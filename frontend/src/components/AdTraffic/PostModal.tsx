import React, { useState, useEffect } from 'react';
import { Box, Flex, Text, TextArea, Button, Heading, Checkbox, TextField, Badge } from '@radix-ui/themes';
import { CalendarIcon, ImageIcon, TrashIcon } from '@radix-ui/react-icons';
import { Client, SocialPost, PostFormData, Platform } from './types';
import { api } from '../../services/api';

interface PostModalProps {
  client: Client;
  post: SocialPost | null;
  onSave: () => void;
  onCancel: () => void;
  onDelete?: (postId: string) => void;
}

export const PostModal: React.FC<PostModalProps> = ({
  client,
  post,
  onSave,
  onCancel,
  onDelete
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
      // Ensure platforms is an array
      let platforms = post.platforms;
      if (!Array.isArray(platforms)) {
        // If it's a string, try to parse it
        if (typeof platforms === 'string') {
          try {
            platforms = JSON.parse(platforms);
          } catch {
            // If parsing fails, default to Facebook
            platforms = [Platform.FACEBOOK];
          }
        } else {
          platforms = [Platform.FACEBOOK];
        }
      }

      // Ensure media_urls is an array
      let mediaUrls = post.media_urls || [];
      if (!Array.isArray(mediaUrls)) {
        if (typeof mediaUrls === 'string') {
          try {
            mediaUrls = JSON.parse(mediaUrls);
          } catch {
            mediaUrls = [];
          }
        } else {
          mediaUrls = [];
        }
      }

      setFormData({
        content: post.content,
        platforms: platforms,
        scheduled_time: new Date(post.scheduled_time).toISOString().slice(0, 16),
        media_urls: mediaUrls,
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

  const handleDelete = async () => {
    if (post && onDelete) {
      if (window.confirm('Are you sure you want to delete this post?')) {
        setLoading(true);
        try {
          await api.delete(`/api/ad-traffic/posts/${post.id}`);
          onDelete(post.id);
        } catch (err: any) {
          setError(err.response?.data?.detail || 'Failed to delete post');
          setLoading(false);
        }
      }
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
    <Box style={{ padding: '2rem' }}>
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

          {/* Video Preview Section */}
          {((formData.media_urls && formData.media_urls.length > 0) || post?.video_clip) && (
            <Box>
              <Text size="2" weight="medium">Video Preview</Text>
              <Box style={{ 
                backgroundColor: 'var(--gray-2)', 
                borderRadius: '8px',
                marginTop: '0.5rem',
                overflow: 'hidden'
              }}>
                {/* Video Preview */}
                <Box style={{ position: 'relative', paddingBottom: '56.25%', height: 0 }}>
                  <video
                    controls
                    style={{
                      position: 'absolute',
                      top: 0,
                      left: 0,
                      width: '100%',
                      height: '100%',
                      backgroundColor: 'black'
                    }}
                  >
                    <source 
                      src={formData.media_urls?.[0] || post?.video_clip?.video_url} 
                      type="video/mp4" 
                    />
                    Your browser does not support the video tag.
                  </video>
                </Box>
                
                {/* Video Info - only show if there's a video_clip with metadata */}
                {post?.video_clip && (
                  <Box style={{ padding: '1rem' }}>
                    <Flex justify="between" align="start">
                      <Box>
                        <Text size="3" weight="medium">{post.video_clip.title}</Text>
                        {post.video_clip.description && (
                          <Text size="2" color="gray" style={{ marginTop: '0.25rem' }}>
                            {post.video_clip.description}
                          </Text>
                        )}
                      </Box>
                      <Badge variant="soft">
                        {Math.round(post.video_clip.duration)}s
                      </Badge>
                    </Flex>
                    
                    {post.video_clip.suggested_hashtags && post.video_clip.suggested_hashtags.length > 0 && (
                      <Flex gap="2" wrap="wrap" style={{ marginTop: '1rem' }}>
                        {post.video_clip.suggested_hashtags.map((tag, index) => (
                          <Badge key={index} variant="outline" size="1">
                            {tag}
                          </Badge>
                        ))}
                      </Flex>
                    )}
                  </Box>
                )}
              </Box>
            </Box>
          )}

          {error && (
            <Text size="2" color="red">{error}</Text>
          )}

          <Flex gap="3" justify="end">
            {post && onDelete && (
              <Button 
                type="button" 
                variant="soft" 
                color="red"
                onClick={handleDelete}
                disabled={loading}
                style={{ marginRight: 'auto' }}
              >
                <TrashIcon /> Delete Post
              </Button>
            )}
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
