"use client";

import { Badge } from "@chakra-ui/react";
import type { JobStatus } from "@/types/api";

interface JobStatusBadgeProps {
  status: JobStatus;
}

const statusColorMap: Record<JobStatus, string> = {
  pending: "gray",
  ingesting: "blue",
  ingested: "cyan",
  editing: "blue",
  edited: "cyan",
  clipping: "blue",
  clipped: "cyan",
  scheduling: "blue",
  complete: "green",
  failed: "red",
};

export function JobStatusBadge({ status }: JobStatusBadgeProps) {
  return (
    <Badge colorPalette={statusColorMap[status]}>
      {status}
    </Badge>
  );
}
