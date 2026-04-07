import { apiClient } from "../api-client";
import type { ClipListResponse, ClipResponse } from "@/types/api";

export const clipsApi = {
  list: (params?: { job_id?: string; skip?: number; limit?: number }) => {
    const searchParams = new URLSearchParams();
    if (params?.job_id) searchParams.set("job_id", params.job_id);
    if (params?.skip) searchParams.set("skip", String(params.skip));
    if (params?.limit) searchParams.set("limit", String(params.limit));
    const qs = searchParams.toString();
    return apiClient.get<ClipListResponse>(`/api/clips${qs ? `?${qs}` : ""}`);
  },
  get: (id: string) => apiClient.get<ClipResponse>(`/api/clips/${id}`),
};
