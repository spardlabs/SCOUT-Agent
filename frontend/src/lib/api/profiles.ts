import { apiClient } from "../api-client";
import type { ProfileCreate, ProfileResponse } from "@/types/api";

export const profilesApi = {
  get: () => apiClient.get<ProfileResponse>("/api/profiles"),
  create: (data: ProfileCreate) =>
    apiClient.post<ProfileResponse>("/api/profiles", data),
  update: (data: Partial<ProfileCreate>) =>
    apiClient.patch<ProfileResponse>("/api/profiles", data),
};
