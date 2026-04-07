"use client";

import { useState } from "react";
import { Box, Heading, Stack } from "@chakra-ui/react";
import { useJobs } from "@/hooks/useJobs";
import { JobsTable } from "@/components/jobs/JobsTable";
import { Pagination } from "@/components/shared/Pagination";
import { EmptyState } from "@/components/shared/EmptyState";
import { LuFileAudio } from "react-icons/lu";

const PAGE_SIZE = 10;

export default function JobsPage() {
  const [page, setPage] = useState(1);
  const { data, isLoading } = useJobs({
    skip: (page - 1) * PAGE_SIZE,
    limit: PAGE_SIZE,
  });

  return (
    <Stack gap={6}>
      <Heading size="lg">Jobs</Heading>

      {!isLoading && data && data.jobs.length === 0 ? (
        <EmptyState
          icon={<LuFileAudio />}
          title="No jobs yet"
          description="Upload a podcast episode to create your first job."
        />
      ) : (
        <Box bg="white" borderRadius="lg" shadow="sm" p={4}>
          <JobsTable jobs={data?.jobs ?? []} isLoading={isLoading} />
        </Box>
      )}

      {data && data.total > PAGE_SIZE && (
        <Pagination
          page={page}
          pageSize={PAGE_SIZE}
          total={data.total}
          onChange={setPage}
        />
      )}
    </Stack>
  );
}
