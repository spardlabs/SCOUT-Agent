import { apiClient } from "../api-client";
import type { UserCreateResponse, UserResponse } from "@/types/api";

export const usersApi = {
  me: () => apiClient.get<UserResponse>("/api/users/me"),
  create: (data: { email: string; name: string }) =>
    apiClient.post<UserCreateResponse>("/api/users", data),
};
