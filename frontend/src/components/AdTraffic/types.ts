export interface Client {
  id: string;
  user_id: string;
  name: string;
  company_name?: string;
  email?: string;
  phone?: string;
  website?: string;
  industry?: string;
  description?: string;
  brand_voice?: string;
  target_audience?: string;
  brand_colors?: string[];
  logo_url?: string;
  social_accounts: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface SocialPost {
  id: string;
  client_id: string;
  campaign_id?: string;
  content: string;
  platforms: Platform[];
  media_urls: string[];
  video_clip?: VideoClip;
  scheduled_time: string;
  status: PostStatus;
  published_at?: string;
  platform_data: Record<string, any>;
  created_at: string;
  updated_at: string;
  campaign_name?: string;
}

export interface Campaign {
  id: string;
  client_id: string;
  name: string;
  original_video_url: string;
  duration_weeks: number;
  platforms: Platform[];
  status: CampaignStatus;
  progress: number;
  error_message?: string;
  created_at: string;
  updated_at: string;
}

export interface VideoClip {
  id: string;
  campaign_id: string;
  title: string;
  description?: string;
  duration: number;
  start_time: number;
  end_time: number;
  video_url: string;
  thumbnail_url?: string;
  platform_versions: Record<string, any>;
  suggested_caption?: string;
  suggested_hashtags: string[];
  content_type?: string;
  created_at: string;
}

export enum Platform {
  FACEBOOK = 'facebook',
  INSTAGRAM = 'instagram',
  TIKTOK = 'tiktok'
}

export enum PostStatus {
  DRAFT = 'DRAFT',
  SCHEDULED = 'SCHEDULED',
  PENDING_APPROVAL = 'PENDING_APPROVAL',
  APPROVED = 'APPROVED',
  PUBLISHED = 'PUBLISHED',
  FAILED = 'FAILED'
}

export enum CampaignStatus {
  PROCESSING = 'processing',
  READY = 'ready',
  FAILED = 'failed'
}

export interface ClientFormData {
  name: string;
  company_name?: string;
  email?: string;
  phone?: string;
  website?: string;
  industry?: string;
  description?: string;
  brand_voice?: string;
  target_audience?: string;
  brand_colors?: string[];
  logo_url?: string;
}

export interface PostFormData {
  content: string;
  platforms: Platform[];
  scheduled_time: string;
  media_urls?: string[];
  video_clip_id?: string;
}

export interface CampaignFormData {
  name: string;
  duration_weeks: number;
  platforms: Platform[];
} 