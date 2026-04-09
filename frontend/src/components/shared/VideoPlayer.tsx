"use client";

import { Box } from "@chakra-ui/react";

interface VideoPlayerProps {
  src: string;
  poster?: string;
}

export function VideoPlayer({ src, poster }: VideoPlayerProps) {
  return (
    <Box borderRadius="lg" overflow="hidden">
      <video
        src={src}
        poster={poster}
        controls
        style={{ width: "100%", display: "block" }}
      />
    </Box>
  );
}
