import { apiClient } from "../api-client";
import type { JobListResponse, JobResponse } from "@/types/api";

export const jobsApi = {
  list: (params?: { skip?: number; limit?: number }) => {
    const searchParams = new URLSearchParams();
    if (params?.skip) searchParams.set("skip", String(params.skip));
    if (params?.limit) searchParams.set("limit", String(params.limit));
    const qs = searchParams.toString();
    return apiClient.get<JobListResponse>(`/api/jobs${qs ? `?${qs}` : ""}`);
  },
  get: (id: string) => apiClient.get<JobResponse>(`/api/jobs/${id}`),
};
