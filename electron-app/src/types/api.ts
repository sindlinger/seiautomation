export interface Token {
  access_token: string;
  token_type: string;
}

export interface User {
  id: number;
  email: string;
  full_name?: string | null;
  is_active: boolean;
  is_admin: boolean;
  allow_auto_credentials: boolean;
}

export interface TaskDefinition {
  name: string;
  slug: string;
  description: string;
}

export interface TaskRunRequest {
  task_slug: string;
  headless: boolean;
  auto_credentials: boolean;
  bloco_id?: number | null;
  limit?: number | null;
  dev_mode?: boolean | null;
}

export interface TaskRun {
  id: string;
  task_name: string;
  status: string;
  log: string;
  created_at: string;
  finished_at?: string | null;
  params?: unknown;
}
