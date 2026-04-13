export type SessionStatus = "draft" | "in_progress" | "scheduled" | "published";

export interface Session {
  id: number;
  title: string;
  topic: string | null;
  lang: string;
  step: number;
  status: SessionStatus;
  created_at: string;
  updated_at: string | null;
}

export interface Scene {
  id: number;
  session_id: number;
  order: number;
  script_text: string;
  emotion_tag: string | null;
  image_path: string | null;
  audio_path: string | null;
  video_path: string | null;
  approved: boolean;
}

export interface ScheduleEntry {
  id: number;
  session_id: number;
  post_time: string;
  caption: string | null;
  hashtags: string | null;
  tiktok_post_id: string | null;
  status: string;
}

export interface TrendTopic {
  topic: string;
  score: number;
  source: string;
}

export interface MiloImage {
  filename: string;
  tags: string[];
  path: string;
  url: string;
}

export interface ChatMessage {
  role: "user" | "ai";
  text: string;
  timestamp: number;
}

export interface Character {
  id: number
  name: string
  personality: string | null
  char_description: string | null
  ref_image_count: number
  fal_ready: boolean
  created_at: string | null
}
