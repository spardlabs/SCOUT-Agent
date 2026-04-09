"use client";

import { Card, Stack, HStack, Text, Heading } from "@chakra-ui/react";
import Link from "next/link";
import { useJobs } from "@/hooks/useJobs";
import { JobStatusBadge } from "@/components/jobs/JobStatusBadge";
import { EmptyState } from "@/components/shared/EmptyState";
import { LoadingSkeleton } from "@/components/shared/LoadingSkeleton";
import { LuFileAudio } from "react-icons/lu";

function timeAgo(dateStr: string): string {
  const seconds = Math.floor(
    (Date.now() - new Date(dateStr).getTime()) / 1000
  );
  if (seconds < 60) return "just now";
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

export function RecentJobsList() {
  const { data, isLoading } = useJobs({ limit: 5 });

  return (
    <Card.Root shadow="sm" height="100%">
      <Card.Header>
        <Heading size="sm">Recent Jobs</Heading>
      </Card.Header>
      <Card.Body>
        {isLoading && <LoadingSkeleton variant="table" />}
        {!isLoading && (!data || data.jobs.length === 0) && (
          <EmptyState
            icon={<LuFileAudio />}
            title="No jobs yet"
            description="Upload a podcast episode to get started."
          />
        )}
        {data && data.jobs.length > 0 && (
          <Stack gap={3}>
            {data.jobs.map((job) => (
              <Link key={job.id} href={`/jobs/${job.id}`}>
                <HStack
                  justify="space-between"
                  p={3}
                  borderRadius="md"
                  _hover={{ bg: "gray.50" }}
                >
                  <Text fontSize="sm" fontWeight="medium" truncate>
                    {job.source_filename}
                  </Text>
                  <HStack gap={2} flexShrink={0}>
                    <JobStatusBadge status={job.status} />
                    <Text fontSize="xs" color="gray.500">
                      {timeAgo(job.created_at)}
                    </Text>
                  </HStack>
                </HStack>
              </Link>
            ))}
          </Stack>
        )}
      </Card.Body>
    </Card.Root>
  );
}
