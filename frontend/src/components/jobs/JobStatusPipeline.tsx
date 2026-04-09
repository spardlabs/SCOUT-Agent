"use client";

import { Flex, Box, Text } from "@chakra-ui/react";
import type { JobStatus } from "@/types/api";

interface JobStatusPipelineProps {
  status: JobStatus;
}

const stages: JobStatus[] = [
  "pending",
  "ingesting",
  "ingested",
  "editing",
  "edited",
  "clipping",
  "clipped",
  "scheduling",
  "complete",
];

const labelMap: Partial<Record<JobStatus, string>> = {
  ingesting: "Ingest",
  editing: "Edit",
  clipping: "Clip",
  scheduling: "Schedule",
  complete: "Done",
};

export function JobStatusPipeline({ status }: JobStatusPipelineProps) {
  const isFailed = status === "failed";

  // For failed status, find the last known stage (use pending as fallback)
  const currentIndex = isFailed
    ? Math.max(stages.indexOf("pending"), 0)
    : stages.indexOf(status);

  return (
    <Flex align="center" gap={0} py={4}>
      {stages.map((stage, i) => {
        const isPast = i < currentIndex;
        const isCurrent = i === currentIndex;
        const label = labelMap[stage];

        let bg = "transparent";
        let borderColor = "gray.300";
        let borderWidth = "2px";

        if (isPast) {
          bg = "green.500";
          borderColor = "green.500";
        } else if (isCurrent && isFailed) {
          bg = "red.500";
          borderColor = "red.500";
        } else if (isCurrent) {
          bg = "blue.500";
          borderColor = "blue.500";
        }

        return (
          <Flex key={stage} align="center" flex={i < stages.length - 1 ? 1 : undefined}>
            {/* Stage circle */}
            <Flex direction="column" align="center" position="relative">
              <Box
                w="12px"
                h="12px"
                borderRadius="full"
                bg={bg}
                borderWidth={borderWidth}
                borderColor={borderColor}
                position="relative"
                display="flex"
                alignItems="center"
                justifyContent="center"
                animation={isCurrent && !isFailed ? "pulse 2s infinite" : undefined}
                css={
                  isCurrent && !isFailed
                    ? {
                        "@keyframes pulse": {
                          "0%, 100%": { boxShadow: "0 0 0 0 rgba(66, 133, 244, 0.4)" },
                          "50%": { boxShadow: "0 0 0 4px rgba(66, 133, 244, 0)" },
                        },
                        animation: "pulse 2s infinite",
                      }
                    : undefined
                }
              >
                {isCurrent && isFailed && (
                  <Text fontSize="8px" color="white" lineHeight={1} fontWeight="bold">
                    X
                  </Text>
                )}
              </Box>
              {label && (
                <Text
                  fontSize="xs"
                  color={isPast ? "green.600" : isCurrent ? (isFailed ? "red.600" : "blue.600") : "gray.400"}
                  position="absolute"
                  top="18px"
                  whiteSpace="nowrap"
                >
                  {label}
                </Text>
              )}
            </Flex>

            {/* Connector line */}
            {i < stages.length - 1 && (
              <Box
                flex={1}
                h="2px"
                bg={isPast ? "green.500" : "gray.200"}
                mx={1}
              />
            )}
          </Flex>
        );
      })}
    </Flex>
  );
}
