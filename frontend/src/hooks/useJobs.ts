import { useQuery } from "@tanstack/react-query";
import { jobsApi } from "@/lib/api/jobs";
import { queryKeys } from "@/lib/query-keys";
import type { JobStatus } from "@/types/api";

const ACTIVE_STATUSES: JobStatus[] = [
  "pending", "ingesting", "ingested", "editing", "edited",
  "clipping", "clipped", "scheduling",
];

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
    // Auto-poll every 2 seconds while the job is still processing
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      if (status && ACTIVE_STATUSES.includes(status)) {
        return 2000;
      }
      return false;
    },
  });
}
