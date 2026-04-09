"use client";

import { useState } from "react";
import {
  Box,
  Heading,
  Text,
  Card,
  Flex,
  Button,
  Badge,
  VStack,
} from "@chakra-ui/react";
import { useQuery } from "@tanstack/react-query";
import { clipsApi } from "@/lib/api/clips";
import { queryKeys } from "@/lib/query-keys";
import { ClipGrid } from "@/components/clips/ClipGrid";
import { Pagination } from "@/components/shared/Pagination";
import { LoadingSkeleton } from "@/components/shared/LoadingSkeleton";
import type { ClipResponse } from "@/types/api";
import { LuX, LuPlay } from "react-icons/lu";

const BACKEND_URL = "http://localhost:8000";

function ClipPreview({
  clip,
  onClose,
}: {
  clip: ClipResponse;
  onClose: () => void;
}) {
  const apiKey = typeof window !== "undefined" ? localStorage.getItem("scout_api_key") : "";
  const videoUrl = `${BACKEND_URL}/api/media/clips/${clip.id}/video?key=${encodeURIComponent(apiKey || "")}`;

  return (
    <Box
      position="fixed"
      top={0}
      left={0}
      right={0}
      bottom={0}
      bg="blackAlpha.700"
      zIndex={1000}
      display="flex"
      alignItems="center"
      justifyContent="center"
      onClick={onClose}
    >
      <Card.Root
        maxW="800px"
        w="90%"
        maxH="90vh"
        overflow="auto"
        onClick={(e) => e.stopPropagation()}
      >
        <Card.Body p={0}>
          <Box position="relative">
            <video
              controls
              autoPlay
              style={{ width: "100%", maxHeight: "450px", background: "#000" }}
              src={videoUrl}
              // Pass API key via custom fetch - fallback to query param
            >
              Your browser does not support video playback.
            </video>
            <Button
              position="absolute"
              top={2}
              right={2}
              size="sm"
              variant="solid"
              colorPalette="gray"
              onClick={onClose}
            >
              <LuX />
            </Button>
          </Box>

          <VStack align="stretch" p={5} gap={3}>
            <Heading size="md">{clip.title}</Heading>

            {clip.description && (
              <Text color="gray.600" fontSize="sm">
                {clip.description}
              </Text>
            )}

            <Flex gap={2} flexWrap="wrap">
              <Badge colorPalette="blue">
                {Math.floor(clip.duration_seconds / 60)}m{" "}
                {Math.round(clip.duration_seconds % 60)}s
              </Badge>
              <Badge
                colorPalette={
                  clip.virality_score > 0.7
                    ? "green"
                    : clip.virality_score > 0.4
                      ? "yellow"
                      : "red"
                }
              >
                {Math.round(clip.virality_score * 100)}% viral
              </Badge>
              {clip.topics.map((t) => (
                <Badge key={t} variant="subtle">
                  {t}
                </Badge>
              ))}
            </Flex>

            {clip.transcript_text && (
              <Box>
                <Text fontSize="sm" fontWeight="medium" mb={1}>
                  Transcript
                </Text>
                <Box
                  p={3}
                  bg="gray.50"
                  borderRadius="md"
                  fontSize="sm"
                  maxH="150px"
                  overflowY="auto"
                  whiteSpace="pre-wrap"
                >
                  {clip.transcript_text}
                </Box>
              </Box>
            )}

            {clip.platform_variants && Object.keys(clip.platform_variants).length > 0 && (
              <Box>
                <Text fontSize="sm" fontWeight="medium" mb={1}>
                  Platform Variants
                </Text>
                <Flex gap={2}>
                  {Object.keys(clip.platform_variants).map((platform) => (
                    <Badge key={platform} colorPalette="purple">
                      {platform}
                    </Badge>
                  ))}
                </Flex>
              </Box>
            )}
          </VStack>
        </Card.Body>
      </Card.Root>
    </Box>
  );
}

export default function ClipsPage() {
  const [page, setPage] = useState(1);
  const [selectedClip, setSelectedClip] = useState<ClipResponse | null>(null);
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
        onClipClick={(clip: ClipResponse) => setSelectedClip(clip)}
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

      {selectedClip && (
        <ClipPreview clip={selectedClip} onClose={() => setSelectedClip(null)} />
      )}
    </Box>
  );
}
