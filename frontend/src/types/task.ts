export interface TaskCreate {
  title: string;
  description: string;
  use_case?: string | null;
}

export interface TaskResponse {
  id: string;
  title: string;
  description: string;
  use_case: string | null;
  status: string;
  intent: string | null;
  task_metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface TaskListResponse {
  tasks: TaskResponse[];
  total: number;
}