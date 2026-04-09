"use client";

import { Table, Text } from "@chakra-ui/react";
import Link from "next/link";
import type { JobResponse } from "@/types/api";
import { JobStatusBadge } from "@/components/jobs/JobStatusBadge";
import { LoadingSkeleton } from "@/components/shared/LoadingSkeleton";

interface JobsTableProps {
  jobs: JobResponse[];
  isLoading: boolean;
}

function formatDuration(seconds: number | null): string {
  if (seconds == null) return "--";
  const m = Math.floor(seconds / 60);
  const s = Math.round(seconds % 60);
  return `${m}m ${s}s`;
}

function timeAgo(dateStr: string): string {
  const seconds = Math.floor(
    (Date.now() - new Date(dateStr).getTime()) / 1000
  );
  if (seconds < 60) return "just now";
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes} minute${minutes !== 1 ? "s" : ""} ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours} hour${hours !== 1 ? "s" : ""} ago`;
  const days = Math.floor(hours / 24);
  return `${days} day${days !== 1 ? "s" : ""} ago`;
}

export function JobsTable({ jobs, isLoading }: JobsTableProps) {
  if (isLoading) {
    return <LoadingSkeleton variant="table" />;
  }

  return (
    <Table.Root size="sm">
      <Table.Header>
        <Table.Row>
          <Table.ColumnHeader>File</Table.ColumnHeader>
          <Table.ColumnHeader>Status</Table.ColumnHeader>
          <Table.ColumnHeader>Duration</Table.ColumnHeader>
          <Table.ColumnHeader>Created</Table.ColumnHeader>
          <Table.ColumnHeader>Actions</Table.ColumnHeader>
        </Table.Row>
      </Table.Header>
      <Table.Body>
        {jobs.map((job) => (
          <Table.Row key={job.id}>
            <Table.Cell>
              <Text fontWeight="medium" truncate maxW="300px">
                {job.source_filename}
              </Text>
            </Table.Cell>
            <Table.Cell>
              <JobStatusBadge status={job.status} />
            </Table.Cell>
            <Table.Cell>{formatDuration(job.duration_seconds)}</Table.Cell>
            <Table.Cell>
              <Text color="gray.600" fontSize="sm">
                {timeAgo(job.created_at)}
              </Text>
            </Table.Cell>
            <Table.Cell>
              <Link href={`/jobs/${job.id}`}>
                <Text color="blue.500" fontWeight="medium" fontSize="sm" _hover={{ textDecoration: "underline" }}>
                  View
                </Text>
              </Link>
            </Table.Cell>
          </Table.Row>
        ))}
      </Table.Body>
    </Table.Root>
  );
}
