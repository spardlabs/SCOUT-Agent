import { useQuery } from "@tanstack/react-query";
import { jobsApi } from "@/lib/api/jobs";
import { queryKeys } from "@/lib/query-keys";

export function useJobs(params?: { skip?: number; limit?: number }) {
  return useQuery({
    queryKey: queryKeys.jobs.list(params ?? {}),
    queryFn: () => jobsApi.list(params),
  });
}

export function useJob(id: string) {
  return useQuery({
    queryKey: queryKeys.jobs.detail(id),
    queryFn: () => jobsApi.get(id),
    enabled: !!id,
  });
}
