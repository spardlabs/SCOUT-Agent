"use client";

import React from "react";
import {
  Box,
  Heading,
  HStack,
  Text,
  SimpleGrid,
  Stack,
  Card,
} from "@chakra-ui/react";
import { useJob } from "@/hooks/useJobs";
import { useClips } from "@/hooks/useClips";
import { JobStatusBadge } from "@/components/jobs/JobStatusBadge";
import { JobStatusPipeline } from "@/components/jobs/JobStatusPipeline";
import { VideoPlayer } from "@/components/shared/VideoPlayer";
import { LoadingSkeleton } from "@/components/shared/LoadingSkeleton";
import { ClipGrid } from "@/components/clips/ClipGrid";

function formatDate(dateStr: string | null): string {
  if (!dateStr) return "--";
  return new Date(dateStr).toLocaleString();
}

export default function JobDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = React.use(params);
  const { data: job, isLoading } = useJob(id);
  const { data: clipsData } = useClips({ job_id: id });

  if (isLoading || !job) {
    return <LoadingSkeleton variant="detail" />;
  }

  return (
    <Stack gap={6}>
      {/* Header */}
      <HStack gap={4} flexWrap="wrap">
        <Heading size="lg">{job.source_filename}</Heading>
        <JobStatusBadge status={job.status} />
      </HStack>

      <HStack gap={6} fontSize="sm" color="gray.600">
        <Text>Created: {formatDate(job.created_at)}</Text>
        {job.started_at && <Text>Started: {formatDate(job.started_at)}</Text>}
        {job.completed_at && (
          <Text>Completed: {formatDate(job.completed_at)}</Text>
        )}
      </HStack>

      {/* Pipeline */}
      <Box bg="white" borderRadius="lg" shadow="sm" p={4}>
        <JobStatusPipeline status={job.status} />
      </Box>

      {/* Error message */}
      {job.error_message && (
        <Box bg="red.50" borderRadius="lg" p={4} borderWidth="1px" borderColor="red.200">
          <Text color="red.700" fontWeight="medium">
            Error: {job.error_message}
          </Text>
        </Box>
      )}

      {/* Two-column: Video + Transcript */}
      <SimpleGrid columns={{ base: 1, md: 2 }} gap={6}>
        <Card.Root shadow="sm">
          <Card.Header>
            <Heading size="sm">Edited Video</Heading>
          </Card.Header>
          <Card.Body>
            {job.edited_file_url ? (
              <VideoPlayer src={`http://localhost:8000/api/media/jobs/${job.id}/video?key=${encodeURIComponent(typeof window !== "undefined" ? localStorage.getItem("scout_api_key") || "" : "")}`} />
            ) : (
              <Text color="gray.500" fontSize="sm">
                No edited file available yet.
              </Text>
            )}
          </Card.Body>
        </Card.Root>

        <Card.Root shadow="sm">
          <Card.Header>
            <Heading size="sm">Transcript</Heading>
          </Card.Header>
          <Card.Body>
            <Box
              w="100%"
              h="300px"
              p={3}
              borderRadius="md"
              borderWidth="1px"
              borderColor="gray.200"
              fontSize="sm"
              overflowY="auto"
              bg="gray.50"
              whiteSpace="pre-wrap"
            >
              {job.transcript_url ? "Transcript loading..." : "No transcript available."}
            </Box>
          </Card.Body>
        </Card.Root>
      </SimpleGrid>

      {/* Clips section */}
      <Box>
        <Heading size="md" mb={4}>
          Clips
        </Heading>
        <ClipGrid
          clips={clipsData?.clips ?? []}
          onClipClick={(clip) => {
            window.location.href = `/clips/${clip.id}`;
          }}
        />
      </Box>
    </Stack>
  );
}
