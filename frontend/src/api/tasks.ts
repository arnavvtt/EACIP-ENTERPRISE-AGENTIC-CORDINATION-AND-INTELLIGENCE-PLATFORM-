import { apiClient } from "./client";
import type {
  TaskCreate,
  TaskListResponse,
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
};