import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { profilesApi } from "@/lib/api/profiles";
import { queryKeys } from "@/lib/query-keys";
import type { ProfileCreate } from "@/types/api";

export function useProfile() {
  return useQuery({
    queryKey: queryKeys.profile,
    queryFn: () => profilesApi.get(),
  });
}

export function useUpdateProfile() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: Partial<ProfileCreate>) => profilesApi.update(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.profile });
    },
  });
}
