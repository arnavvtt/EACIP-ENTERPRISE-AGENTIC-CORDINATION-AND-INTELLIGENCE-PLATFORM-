import { apiClient } from "./client";
import type {
  ContextWorkspaceResponse,
  CorrelationListResponse,
  IdentifyRequirementsResponse,
  RetrievedRecordListResponse,
  RunCorrelationResponse,
  RunRetrievalResponse,
  TaskCreate,
  TaskListResponse,
  TaskRequirementListResponse,
  TaskResponse,
} from "../types/task";

export const tasksApi = {
  create: async (data: TaskCreate): Promise<TaskResponse> => {
    const res = await apiClient.post<TaskResponse>("/tasks", data);
    return res.data;
  },

  list: async (limit = 100, offset = 0): Promise<TaskListResponse> => {
    const res = await apiClient.get<TaskListResponse>("/tasks", {
      params: { limit, offset },
    });
    return res.data;
  },

  get: async (id: string): Promise<TaskResponse> => {
    const res = await apiClient.get<TaskResponse>(`/tasks/${id}`);
    return res.data;
  },

  understand: async (id: string): Promise<TaskResponse> => {
    const res = await apiClient.post<TaskResponse>(
      `/tasks/${id}/understand`,
    );
    return res.data;
  },

  identifyRequirements: async (
    id: string,
  ): Promise<IdentifyRequirementsResponse> => {
    const res = await apiClient.post<IdentifyRequirementsResponse>(
      `/tasks/${id}/identify-requirements`,
    );
    return res.data;
  },

  getRequirements: async (
    id: string,
  ): Promise<TaskRequirementListResponse> => {
    const res = await apiClient.get<TaskRequirementListResponse>(
      `/tasks/${id}/requirements`,
    );
    return res.data;
  },

  retrieve: async (id: string): Promise<RunRetrievalResponse> => {
    const res = await apiClient.post<RunRetrievalResponse>(
      `/tasks/${id}/retrieve`,
    );
    return res.data;
  },

  getRetrievedRecords: async (
    id: string,
  ): Promise<RetrievedRecordListResponse> => {
    const res = await apiClient.get<RetrievedRecordListResponse>(
      `/tasks/${id}/retrieved-records`,
    );
    return res.data;
  },

  correlate: async (id: string): Promise<RunCorrelationResponse> => {
    const res = await apiClient.post<RunCorrelationResponse>(
      `/tasks/${id}/correlate`,
    );
    return res.data;
  },

  getCorrelations: async (id: string): Promise<CorrelationListResponse> => {
    const res = await apiClient.get<CorrelationListResponse>(
      `/tasks/${id}/correlations`,
    );
    return res.data;
  },

  getContext: async (id: string): Promise<ContextWorkspaceResponse> => {
    const res = await apiClient.get<ContextWorkspaceResponse>(
      `/tasks/${id}/context`,
    );
    return res.data;
  },
};