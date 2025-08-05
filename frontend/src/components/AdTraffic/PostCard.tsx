import React, { useState } from 'react';
import { Box, Card, Flex, Text, Badge, IconButton, DropdownMenu, AlertDialog, Button } from '@radix-ui/themes';
import { 
  DotsHorizontalIcon, 
  Pencil2Icon, 
  TrashIcon,
  CopyIcon,
  EyeOpenIcon,
  VideoIcon,
  CheckIcon 
} from '@radix-ui/react-icons';
import { SocialPost, Platform, PostStatus } from './types';

interface PostCardProps {
  post: SocialPost;
  onEdit: () => void;
  onDelete: () => void;
  onApprove?: (approved: boolean) => void;
  compact?: boolean;
}

export const PostCard: React.FC<PostCardProps> = ({
  post,
  onEdit,
  onDelete,
  onApprove,
  compact = false
}) => {
  const getPlatformIcon = (platform: Platform) => {
    switch (platform) {
      case Platform.FACEBOOK:
        return 'F';
      case Platform.INSTAGRAM:
        return 'I';
      case Platform.TIKTOK:
        return 'T';
      default:
        return '?';
    }
  };

  const getPlatformColor = (platform: Platform) => {
    switch (platform) {
      case Platform.FACEBOOK:
        return 'blue';
      case Platform.INSTAGRAM:
        return 'purple';
      case Platform.TIKTOK:
        return 'gray';
      default:
        return 'gray';
    }
  };

  const getStatusColor = (status: PostStatus) => {
    switch (status) {
      case PostStatus.DRAFT:
        return 'gray';
      case PostStatus.SCHEDULED:
        return 'blue';
      case PostStatus.PENDING_APPROVAL:
        return 'orange';
      case PostStatus.APPROVED:
        return 'green';
      case PostStatus.PUBLISHED:
        return 'green';
      case PostStatus.FAILED:
        return 'red';
      default:
        return 'gray';
    }
  };

  const formatTime = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleTimeString('en-US', { 
      hour: 'numeric', 
      minute: '2-digit',
      hour12: true 
    });
  };

  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);

  const isApproved = post.status === PostStatus.APPROVED || post.status === PostStatus.PUBLISHED;
  const needsApproval = post.status === PostStatus.SCHEDULED || post.status === PostStatus.PENDING_APPROVAL;

  // Debug logging
  console.log('PostCard Debug:', {
    postId: post.id,
    status: post.status,
    isApproved,
    needsApproval,
    hasOnApprove: !!onApprove
  });

  if (compact) {
    return (
      <Card 
        size="1"
        style={{ 
          cursor: 'pointer',
          transition: 'all 0.2s',
          padding: '0.5rem'
        }}
        onClick={onEdit}
      >
        <Flex direction="column" gap="1">
          <Flex justify="between" align="center">
            <Flex gap="1" align="center">
              {post.platforms.map(platform => (
                <Badge 
                  key={platform} 
                  size="1" 
                  variant="solid" 
                  color={getPlatformColor(platform)}
                  style={{ padding: '2px 4px', fontSize: '10px' }}
                >
                  {getPlatformIcon(platform)}
                </Badge>
              ))}
              {post.video_clip && (
                <VideoIcon 
                  width="14" 
                  height="14" 
                  color="var(--purple-9)"
                  style={{ marginLeft: '4px' }}
                />
              )}
            </Flex>
            <Text size="1" color="gray">
              {formatTime(post.scheduled_time)}
            </Text>
          </Flex>
          
          <Text 
            size="1" 
            style={{ 
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              display: '-webkit-box',
              WebkitLineClamp: 2,
              WebkitBoxOrient: 'vertical'
            }}
          >
            {post.content}
          </Text>

          {post.campaign_name && (
            <Badge size="1" variant="soft" color="purple">
              {post.campaign_name}
            </Badge>
          )}
        </Flex>
      </Card>
    );
  }

  return (
    <Card 
      style={{ 
        width: '100%',
        opacity: needsApproval ? 0.7 : 1,
        border: needsApproval ? '1px solid var(--orange-6)' : undefined
      }}
    >
      <Flex direction="column" gap="3">
        <Flex justify="between" align="start">
          <Flex gap="2" align="center">
            {post.platforms.map(platform => (
              <Badge 
                key={platform} 
                variant="solid" 
                color={getPlatformColor(platform)}
              >
                {platform}
              </Badge>
            ))}
            <Badge variant="soft" color={getStatusColor(post.status)}>
              {post.status}
            </Badge>
            {post.campaign_name && (
              <Badge variant="soft" color="purple">
                Campaign: {post.campaign_name}
              </Badge>
            )}
            {isApproved && (
              <Badge variant="soft" color="green">
                <CheckIcon style={{ marginRight: '4px' }} />
                Approved
              </Badge>
            )}
          </Flex>

          <Flex gap="2" align="center">
            {needsApproval && onApprove && (
              <Button 
                size="1" 
                variant="soft" 
                color="green"
                onClick={() => onApprove(true)}
              >
                <CheckIcon />
                Approve
              </Button>
            )}
            <DropdownMenu.Root>
              <DropdownMenu.Trigger>
                <IconButton size="1" variant="ghost">
                  <DotsHorizontalIcon />
                </IconButton>
              </DropdownMenu.Trigger>
              <DropdownMenu.Content>
                <DropdownMenu.Item onClick={onEdit}>
                  <Pencil2Icon /> Edit
                </DropdownMenu.Item>
                <DropdownMenu.Item>
                  <CopyIcon /> Duplicate
                </DropdownMenu.Item>
                <DropdownMenu.Item>
                  <EyeOpenIcon /> Preview
                </DropdownMenu.Item>
                <DropdownMenu.Separator />
                <DropdownMenu.Item color="red" onClick={() => setIsDeleteDialogOpen(true)}>
                  <TrashIcon /> Delete
                </DropdownMenu.Item>
              </DropdownMenu.Content>
            </DropdownMenu.Root>
          </Flex>
        </Flex>

        <Text size="2" style={{ whiteSpace: 'pre-wrap' }}>
          {post.content}
        </Text>

        {post.media_urls && post.media_urls.length > 0 && (
          <Flex gap="2" wrap="wrap">
            {post.media_urls.map((url, index) => (
              <Box
                key={index}
                style={{
                  width: '80px',
                  height: '80px',
                  borderRadius: '4px',
                  overflow: 'hidden',
                  backgroundColor: 'var(--gray-3)'
                }}
              >
                <img 
                  src={url} 
                  alt={`Media ${index + 1}`}
                  style={{ 
                    width: '100%', 
                    height: '100%', 
                    objectFit: 'cover' 
                  }}
                />
              </Box>
            ))}
          </Flex>
        )}

        {post.video_clip && (
          <Card variant="surface">
            <Flex gap="3" align="center">
              <Box
                style={{
                  width: '60px',
                  height: '60px',
                  borderRadius: '4px',
                  overflow: 'hidden',
                  backgroundColor: 'var(--gray-3)'
                }}
              >
                {post.video_clip.thumbnail_url && (
                  <img 
                    src={post.video_clip.thumbnail_url} 
                    alt={post.video_clip.title}
                    style={{ 
                      width: '100%', 
                      height: '100%', 
                      objectFit: 'cover' 
                    }}
                  />
                )}
              </Box>
              <Box>
                <Text size="2" weight="medium">{post.video_clip.title}</Text>
                <Text size="1" color="gray">
                  {Math.round(post.video_clip.duration)}s • {post.video_clip.content_type}
                </Text>
              </Box>
            </Flex>
          </Card>
        )}

        <Flex justify="between" align="center">
          <Text size="1" color="gray">
            Scheduled for {new Date(post.scheduled_time).toLocaleString()}
          </Text>
        </Flex>
      </Flex>

      <AlertDialog.Root open={isDeleteDialogOpen} onOpenChange={setIsDeleteDialogOpen}>
        <AlertDialog.Content maxWidth="450px">
          <AlertDialog.Title>Delete Post</AlertDialog.Title>
          <AlertDialog.Description size="2">
            Are you sure you want to delete this post? This action cannot be undone.
          </AlertDialog.Description>

          <Flex gap="3" mt="4" justify="end">
            <AlertDialog.Cancel>
              <Button variant="soft" color="gray">
                Cancel
              </Button>
            </AlertDialog.Cancel>
            <AlertDialog.Action>
              <Button variant="solid" color="red" onClick={() => {
                onDelete();
                setIsDeleteDialogOpen(false);
              }}>
                Delete
              </Button>
            </AlertDialog.Action>
          </Flex>
        </AlertDialog.Content>
      </AlertDialog.Root>
    </Card>
  );
}; 