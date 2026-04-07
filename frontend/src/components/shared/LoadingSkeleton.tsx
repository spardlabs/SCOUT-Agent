"use client";

import { Box, SimpleGrid, Skeleton, Stack } from "@chakra-ui/react";

interface LoadingSkeletonProps {
  variant: "cards" | "table" | "detail";
}

export function LoadingSkeleton({ variant }: LoadingSkeletonProps) {
  if (variant === "cards") {
    return (
      <SimpleGrid columns={{ base: 1, md: 2, lg: 4 }} gap={4}>
        {Array.from({ length: 4 }).map((_, i) => (
          <Skeleton key={i} height="120px" borderRadius="lg" />
        ))}
      </SimpleGrid>
    );
  }

  if (variant === "table") {
    return (
      <Stack gap={3}>
        {Array.from({ length: 5 }).map((_, i) => (
          <Skeleton key={i} height="40px" borderRadius="md" />
        ))}
      </Stack>
    );
  }

  // detail
  return (
    <Stack gap={4}>
      <Skeleton height="32px" width="40%" borderRadius="md" />
      <Skeleton height="200px" borderRadius="lg" />
      <SimpleGrid columns={{ base: 1, md: 2 }} gap={4}>
        <Skeleton height="80px" borderRadius="md" />
        <Skeleton height="80px" borderRadius="md" />
      </SimpleGrid>
      <Skeleton height="120px" borderRadius="md" />
    </Stack>
  );
}
