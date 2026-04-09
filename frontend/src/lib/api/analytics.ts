import { apiClient } from "../api-client";
import type { WeeklyReportListResponse, WeeklyReportResponse } from "@/types/api";

export const analyticsApi = {
  listReports: (params?: { skip?: number; limit?: number }) => {
    const searchParams = new URLSearchParams();
    if (params?.skip) searchParams.set("skip", String(params.skip));
    if (params?.limit) searchParams.set("limit", String(params.limit));
    const qs = searchParams.toString();
    return apiClient.get<WeeklyReportListResponse>(
      `/api/analytics/reports${qs ? `?${qs}` : ""}`,
    );
  },
  getReport: (id: string) =>
    apiClient.get<WeeklyReportResponse>(`/api/analytics/reports/${id}`),
};
