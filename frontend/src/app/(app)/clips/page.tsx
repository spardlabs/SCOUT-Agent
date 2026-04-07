"use client";

import { useState } from "react";
import { Box, Heading, SimpleGrid } from "@chakra-ui/react";
import { useQuery } from "@tanstack/react-query";
import { clipsApi } from "@/lib/api/clips";
import { queryKeys } from "@/lib/query-keys";
import { ClipGrid } from "@/components/clips/ClipGrid";
import { Pagination } from "@/components/shared/Pagination";
import { LoadingSkeleton } from "@/components/shared/LoadingSkeleton";
import type { ClipResponse } from "@/types/api";

export default function ClipsPage() {
  const [page, setPage] = useState(1);
  const pageSize = 12;

  const { data, isLoading } = useQuery({
    queryKey: queryKeys.clips.list({ page }),
    queryFn: () => clipsApi.list({ skip: (page - 1) * pageSize, limit: pageSize }),
  });

  if (isLoading) return <LoadingSkeleton variant="cards" />;

  return (
    <Box>
      <Heading size="lg" mb={6}>
        Clips
      </Heading>

      <ClipGrid
        clips={data?.clips || []}
        onClipClick={(clip: ClipResponse) => {
          // Could open a preview modal - for now just log
          console.log("Clip clicked:", clip.title);
        }}
      />

      {data && data.total > pageSize && (
        <Box mt={6}>
          <Pagination
            page={page}
            pageSize={pageSize}
            total={data.total}
            onChange={setPage}
          />
        </Box>
      )}
    </Box>
  );
}
