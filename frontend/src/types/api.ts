// TypeScript types mirroring backend Pydantic schemas

export interface UserResponse {
  id: string;
  email: string;
  name: string;
  created_at: string;
}

export interface UserCreateResponse {
  user: UserResponse;
  api_key: string;
}

export interface ProfileCreate {
  silence_threshold_ms?: number;
  silence_action?: string;
  target_lufs?: number;
  intro_asset_url?: string | null;
  outro_asset_url?: string | null;
  logo_asset_url?: string | null;
  brand_color_primary?: string;
  brand_color_secondary?: string;
  brand_font?: string;
  caption_style?: Record<string, unknown>;
  topics?: string[];
  virality_preferences?: Record<string, number>;
  target_platforms?: string[];
  clip_length_range?: { min_seconds: number; max_seconds: number };
  editing_style?: string;
}

export interface ProfileResponse extends Required<ProfileCreate> {
  id: string;
  user_id: string;
  created_at: string;
  updated_at: string;
}

export type JobStatus =
  | "pending"
  | "ingesting"
  | "ingested"
  | "editing"
  | "edited"
  | "clipping"
  | "clipped"
  | "scheduling"
  | "complete"
  | "failed";

export interface JobResponse {
  id: string;
  user_id: string;
  status: JobStatus;
  source_filename: string;
  raw_file_url: string | null;
  edited_file_url: string | null;
  transcript_url: string | null;
  duration_seconds: number | null;
  file_metadata: Record<string, unknown> | null;
  error_message: string | null;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface JobListResponse {
  jobs: JobResponse[];
  total: number;
}

export type ClipStatus = "generated" | "scheduled" | "posted" | "failed";

export interface ClipResponse {
  id: string;
  job_id: string;
  title: string;
  description: string | null;
  start_time_seconds: number;
  end_time_seconds: number;
  duration_seconds: number;
  clip_file_url: string;
  thumbnail_url: string | null;
  platform_variants: Record<string, string> | null;
  virality_score: number;
  topics: string[];
  transcript_text: string | null;
  status: ClipStatus;
  created_at: string;
}

export interface ClipListResponse {
  clips: ClipResponse[];
  total: number;
}

export type Platform = "tiktok" | "instagram" | "youtube" | "twitter" | "linkedin";

export interface SocialAccountResponse {
  id: string;
  platform: Platform;
  platform_username: string;
  is_active: boolean;
}

export interface WeeklyReportResponse {
  id: string;
  user_id: string;
  week_start: string;
  week_end: string;
  report_data: Record<string, unknown>;
  narrative: string;
  delivered_at: string | null;
  created_at: string;
}

export interface WeeklyReportListResponse {
  reports: WeeklyReportResponse[];
  total: number;
}
