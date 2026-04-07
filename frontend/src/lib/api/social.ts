import { apiClient } from "../api-client";
import type { SocialAccountResponse, Platform } from "@/types/api";

export const socialApi = {
  list: () =>
    apiClient.get<SocialAccountResponse[]>("/api/social/accounts"),
  connect: (data: {
    platform: Platform;
    platform_user_id: string;
    platform_username: string;
    access_token: string;
    refresh_token?: string;
  }) => apiClient.post<SocialAccountResponse>("/api/social/accounts", data),
  disconnect: (accountId: string) =>
    apiClient.delete(`/api/social/accounts/${accountId}`),
};
