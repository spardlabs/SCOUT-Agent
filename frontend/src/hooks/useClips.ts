import { useQuery } from "@tanstack/react-query";
import { clipsApi } from "@/lib/api/clips";
import { queryKeys } from "@/lib/query-keys";

export function useClips(params?: {
  job_id?: string;
  skip?: number;
  limit?: number;
}) {
  return useQuery({
    queryKey: queryKeys.clips.list(params ?? {}),
    queryFn: () => clipsApi.list(params),
  });
}
