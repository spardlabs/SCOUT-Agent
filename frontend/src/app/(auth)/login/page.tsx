"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  Box,
  Button,
  Card,
  Heading,
  Input,
  Text,
  Flex,
  IconButton,
} from "@chakra-ui/react";
import { LuEye, LuEyeOff } from "react-icons/lu";
import { useAuth } from "@/providers/AuthProvider";

export default function LoginPage() {
  const [apiKey, setApiKey] = useState("");
  const [showKey, setShowKey] = useState(false);
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { login } = useAuth();
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!apiKey.trim()) {
      setError("API key is required");
      return;
    }

    setError("");
    setIsSubmitting(true);

    try {
      login(apiKey.trim());
      router.replace("/dashboard");
    } catch {
      setError("Invalid API key. Please try again.");
      setIsSubmitting(false);
    }
  };

  return (
    <Card.Root bg="white" shadow="sm" borderRadius="lg">
      <Card.Body p={8}>
        <form onSubmit={handleSubmit}>
          <Heading size="lg" mb={2}>
            Welcome back
          </Heading>
          <Text color="gray.500" mb={6} fontSize="sm">
            Enter your API key to sign in
          </Text>

          <Box mb={4}>
            <Text fontSize="sm" fontWeight="medium" mb={1}>
              API Key
            </Text>
            <Flex>
              <Input
                type={showKey ? "text" : "password"}
                placeholder="Enter your API key"
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                flex={1}
              />
              <IconButton
                aria-label={showKey ? "Hide API key" : "Show API key"}
                variant="ghost"
                ml={-10}
                onClick={() => setShowKey(!showKey)}
              >
                {showKey ? <LuEyeOff /> : <LuEye />}
              </IconButton>
            </Flex>
          </Box>

          {error && (
            <Text color="red.500" fontSize="sm" mb={4}>
              {error}
            </Text>
          )}

          <Button
            type="submit"
            w="100%"
            bg="brand.500"
            color="white"
            loading={isSubmitting}
            mb={4}
          >
            Sign in
          </Button>

          <Text fontSize="sm" textAlign="center" color="gray.500">
            Don&apos;t have an account?{" "}
            <Link href="/register" style={{ color: "#1a1a2e", fontWeight: 600 }}>
              Create one
            </Link>
          </Text>
        </form>
      </Card.Body>
    </Card.Root>
  );
}
