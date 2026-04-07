"use client";

import { Badge } from "@chakra-ui/react";

interface ViralityScoreBadgeProps {
  score: number;
}

export function ViralityScoreBadge({ score }: ViralityScoreBadgeProps) {
  const percentage = Math.round(score * 100);
  const colorPalette = score > 0.7 ? "green" : score > 0.4 ? "yellow" : "red";

  return (
    <Badge colorPalette={colorPalette}>
      {percentage}%
    </Badge>
  );
}
