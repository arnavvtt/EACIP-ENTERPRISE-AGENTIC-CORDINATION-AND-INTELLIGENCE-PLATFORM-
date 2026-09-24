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
// =====================================================================
// Requirements (Stage 5)
// =====================================================================

export interface TaskRequirement {
  id: string;
  task_id: string;
  requirement_type: string;
  description: string;
  is_mandatory: boolean;
  source_hint: string | null;
  priority: number;
  requirement_metadata: Record<string, unknown>;
}

export interface TaskRequirementListResponse {
  requirements: TaskRequirement[];
  total: number;
}

export interface IdentifyRequirementsResponse {
  task_id: string;
  total_requirements: number;
  identified_at: string;
}
// =====================================================================
// Retrieved Records (Stage 6)
// =====================================================================

export interface RetrievedRecord {
  id: string;
  task_id: string;
  requirement_id: string | null;
  source_record_id: string;
  retrieval_method: string;
  relevance_score: number | null;
  is_selected: boolean;
  retrieval_metadata: {
    source_key?: string;
    record_type?: string;
    external_id?: string;
    match_reason?: string;
    requirement_type?: string;
  };
}

export interface RetrievedRecordListResponse {
  records: RetrievedRecord[];
  total: number;
}

export interface RunRetrievalResponse {
  task_id: string;
  total_retrieved: number;
  requirements_processed: number;
  requirements_skipped: number;
  sources_used: string[];
  run_at: string;
}