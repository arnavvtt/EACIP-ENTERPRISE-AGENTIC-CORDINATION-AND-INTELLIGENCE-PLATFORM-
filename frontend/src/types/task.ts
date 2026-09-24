// =====================================================================
// Tasks (Stage 3)
// =====================================================================

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

// =====================================================================
// Correlations (Stage 8)
// =====================================================================

export interface Correlation {
  id: string;
  task_id: string;
  record_a_id: string;
  record_b_id: string;
  relationship_type: string;
  basis: string;
  confidence: number;
  is_verified: boolean;
  correlation_metadata: {
    anchor_record_id?: string;
    anchor_external_id?: string;
    anchor_matched_field?: string;
    anchor_matched_value?: string;
    matched_value?: string;
    matched_fields?: string[];
    all_matched_values?: Array<{ field: string; value: string }>;
    record_a_external_id?: string;
    record_b_external_id?: string;
    pair_kind?: "anchor" | "secondary";
  };
}

export interface CorrelationListResponse {
  correlations: Correlation[];
  total: number;
}

export interface RunCorrelationResponse {
  task_id: string;
  total_correlations: number;
  anchor_external_id: string | null;
  basis_breakdown: Record<string, number>;
  run_at: string;
}

// =====================================================================
// Context Workspace (Stage 7 + 8)
// =====================================================================

export interface ContextWorkspaceResponse {
  task: TaskResponse;
  requirements: TaskRequirement[];
  retrieved_records: RetrievedRecord[];
  correlations: Correlation[];
}