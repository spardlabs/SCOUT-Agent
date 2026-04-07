"use client";

import { Card, Heading, HStack, Text, Badge, Flex } from "@chakra-ui/react";
import type { ClipResponse } from "@/types/api";
import { ViralityScoreBadge } from "@/components/clips/ViralityScoreBadge";

interface ClipCardProps {
  clip: ClipResponse;
  onClick?: (clip: ClipResponse) => void;
}

function formatDuration(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = Math.round(seconds % 60);
  return `${m}m ${s}s`;
}

function viralityColor(score: number): string {
  if (score > 0.7) return "green.400";
  if (score > 0.4) return "yellow.400";
  return "red.400";
}

export function ClipCard({ clip, onClick }: ClipCardProps) {
  return (
    <Card.Root
      shadow="sm"
      cursor={onClick ? "pointer" : undefined}
      onClick={() => onClick?.(clip)}
      _hover={onClick ? { shadow: "md" } : undefined}
      borderTopWidth="3px"
      borderTopColor={viralityColor(clip.virality_score)}
    >
      <Card.Body>
        <Flex direction="column" gap={3}>
          <Heading size="sm" lineClamp={2}>
            {clip.title}
          </Heading>

          <HStack justify="space-between">
            <Text fontSize="sm" color="gray.600">
              {formatDuration(clip.duration_seconds)}
            </Text>
            <ViralityScoreBadge score={clip.virality_score} />
          </HStack>

          {clip.topics.length > 0 && (
            <Flex gap={1} flexWrap="wrap">
              {clip.topics.map((topic) => (
                <Badge key={topic} variant="subtle" colorPalette="gray" size="sm">
                  {topic}
                </Badge>
              ))}
            </Flex>
          )}
        </Flex>
      </Card.Body>
    </Card.Root>
  );
}
