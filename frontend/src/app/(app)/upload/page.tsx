"use client";

import { useCallback, useState, useRef } from "react";
import { useRouter } from "next/navigation";
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
import { LuUpload, LuFile, LuCheck, LuX } from "react-icons/lu";
import { uploadApi } from "@/lib/api/upload";
import { useQueryClient } from "@tanstack/react-query";
import { queryKeys } from "@/lib/query-keys";

type UploadState = "idle" | "dragging" | "uploading" | "success" | "error";

export default function UploadPage() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [state, setState] = useState<UploadState>("idle");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState("");
  const [jobId, setJobId] = useState<string | null>(null);

  const ALLOWED = [".mp4", ".mov", ".mkv", ".avi", ".webm"];

  const validateFile = (file: File): string | null => {
    const ext = "." + file.name.split(".").pop()?.toLowerCase();
    if (!ALLOWED.includes(ext)) {
      return `Unsupported format. Allowed: ${ALLOWED.join(", ")}`;
    }
    if (file.size > 10 * 1024 * 1024 * 1024) {
      return "File too large. Maximum 10GB.";
    }
    return null;
  };

  const handleFile = (file: File) => {
    const validationError = validateFile(file);
    if (validationError) {
      setError(validationError);
      setState("error");
      return;
    }
    setSelectedFile(file);
    setError("");
    setState("idle");
  };

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setState("idle");
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setState("dragging");
  }, []);

  const handleDragLeave = useCallback(() => {
    setState("idle");
  }, []);

  const handleUpload = async () => {
    if (!selectedFile) return;

    setState("uploading");
    setProgress(0);
    setError("");

    // Simulate progress since fetch doesn't give upload progress
    const progressInterval = setInterval(() => {
      setProgress((p) => Math.min(p + 5, 90));
    }, 300);

    try {
      const job = await uploadApi.uploadFile(selectedFile);
      clearInterval(progressInterval);
      setProgress(100);
      setJobId(job.id);
      setState("success");
      queryClient.invalidateQueries({ queryKey: queryKeys.jobs.all });
    } catch (err) {
      clearInterval(progressInterval);
      setError(err instanceof Error ? err.message : "Upload failed");
      setState("error");
    }
  };

  const formatSize = (bytes: number) => {
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    if (bytes < 1024 * 1024 * 1024)
      return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
    return `${(bytes / (1024 * 1024 * 1024)).toFixed(2)} GB`;
  };

  return (
    <Box maxW="700px" mx="auto">
      <Heading size="lg" mb={2}>
        Upload Episode
      </Heading>
      <Text color="gray.500" mb={6}>
        Upload your raw podcast video and our AI agents will handle the rest.
      </Text>

      {/* Drop Zone */}
      <Card.Root
        mb={6}
        borderWidth="2px"
        borderStyle="dashed"
        borderColor={
          state === "dragging"
            ? "blue.400"
            : state === "error"
              ? "red.300"
              : "gray.200"
        }
        bg={state === "dragging" ? "blue.50" : "white"}
        cursor="pointer"
        onClick={() => fileInputRef.current?.click()}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        transition="all 0.2s"
        _hover={{ borderColor: "blue.300", bg: "gray.50" }}
      >
        <Card.Body py={12}>
          <VStack gap={3}>
            <Flex
              w="64px"
              h="64px"
              borderRadius="full"
              bg="blue.50"
              align="center"
              justify="center"
            >
              <LuUpload size={28} color="#3182CE" />
            </Flex>
            <Text fontWeight="medium" fontSize="lg">
              Drag & drop your video here
            </Text>
            <Text color="gray.400" fontSize="sm">
              or click to browse - MP4, MOV, MKV, AVI, WebM up to 10GB
            </Text>
          </VStack>
        </Card.Body>
      </Card.Root>

      <input
        ref={fileInputRef}
        type="file"
        accept=".mp4,.mov,.mkv,.avi,.webm"
        style={{ display: "none" }}
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file) handleFile(file);
        }}
      />

      {/* Selected File */}
      {selectedFile && state !== "success" && (
        <Card.Root mb={4}>
          <Card.Body>
            <Flex align="center" gap={3}>
              <Flex
                w="40px"
                h="40px"
                borderRadius="md"
                bg="gray.100"
                align="center"
                justify="center"
                flexShrink={0}
              >
                <LuFile size={20} />
              </Flex>
              <Box flex={1}>
                <Text fontWeight="medium" fontSize="sm" lineClamp={1}>
                  {selectedFile.name}
                </Text>
                <Text color="gray.400" fontSize="xs">
                  {formatSize(selectedFile.size)}
                </Text>
              </Box>
              <Button
                size="sm"
                variant="ghost"
                onClick={(e) => {
                  e.stopPropagation();
                  setSelectedFile(null);
                  setState("idle");
                }}
              >
                <LuX />
              </Button>
            </Flex>

            {/* Progress Bar */}
            {state === "uploading" && (
              <Box mt={3}>
                <Box
                  h="6px"
                  bg="gray.100"
                  borderRadius="full"
                  overflow="hidden"
                >
                  <Box
                    h="100%"
                    bg="blue.500"
                    borderRadius="full"
                    width={`${progress}%`}
                    transition="width 0.3s"
                  />
                </Box>
                <Text fontSize="xs" color="gray.400" mt={1}>
                  Uploading... {progress}%
                </Text>
              </Box>
            )}
          </Card.Body>
        </Card.Root>
      )}

      {/* Error */}
      {error && (
        <Card.Root mb={4} borderColor="red.200" borderWidth="1px" bg="red.50">
          <Card.Body py={3}>
            <Text color="red.600" fontSize="sm">
              {error}
            </Text>
          </Card.Body>
        </Card.Root>
      )}

      {/* Success */}
      {state === "success" && (
        <Card.Root mb={4} borderColor="green.200" borderWidth="1px" bg="green.50">
          <Card.Body>
            <Flex align="center" gap={3}>
              <Flex
                w="40px"
                h="40px"
                borderRadius="full"
                bg="green.100"
                align="center"
                justify="center"
              >
                <LuCheck size={20} color="#38A169" />
              </Flex>
              <Box>
                <Text fontWeight="medium" color="green.700">
                  Upload complete!
                </Text>
                <Text fontSize="sm" color="green.600">
                  {selectedFile?.name} has been queued for processing.
                </Text>
              </Box>
            </Flex>
          </Card.Body>
        </Card.Root>
      )}

      {/* Actions */}
      <Flex gap={3}>
        {state !== "success" ? (
          <Button
            colorPalette="blue"
            size="lg"
            onClick={handleUpload}
            disabled={!selectedFile || state === "uploading"}
            loading={state === "uploading"}
            flex={1}
          >
            <LuUpload /> Upload & Process
          </Button>
        ) : (
          <>
            <Button
              colorPalette="blue"
              size="lg"
              onClick={() => router.push(`/jobs/${jobId}`)}
              flex={1}
            >
              View Job
            </Button>
            <Button
              variant="outline"
              size="lg"
              onClick={() => {
                setSelectedFile(null);
                setState("idle");
                setJobId(null);
                setProgress(0);
              }}
              flex={1}
            >
              Upload Another
            </Button>
          </>
        )}
      </Flex>
    </Box>
  );
}
