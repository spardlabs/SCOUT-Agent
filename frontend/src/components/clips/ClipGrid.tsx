"use client";

import { SimpleGrid } from "@chakra-ui/react";
import type { ClipResponse } from "@/types/api";
import { ClipCard } from "@/components/clips/ClipCard";
import { EmptyState } from "@/components/shared/EmptyState";
import { LuFilm } from "react-icons/lu";

interface ClipGridProps {
  clips: ClipResponse[];
  onClipClick?: (clip: ClipResponse) => void;
}

export function ClipGrid({ clips, onClipClick }: ClipGridProps) {
  if (clips.length === 0) {
    return (
      <EmptyState
        icon={<LuFilm />}
        title="No clips yet"
        description="Clips will appear here once a job finishes processing."
      />
    );
  }

  return (
    <SimpleGrid columns={{ base: 1, md: 2, lg: 3 }} gap={4}>
      {clips.map((clip) => (
        <ClipCard key={clip.id} clip={clip} onClick={onClipClick} />
      ))}
    </SimpleGrid>
  );
}
