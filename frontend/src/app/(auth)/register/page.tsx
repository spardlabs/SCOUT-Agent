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
import { LuCopy, LuCheck } from "react-icons/lu";
import { useAuth } from "@/providers/AuthProvider";
import { usersApi } from "@/lib/api/users";

export default function RegisterPage() {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [generatedKey, setGeneratedKey] = useState("");
  const [copied, setCopied] = useState(false);
  const { login } = useAuth();
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim() || !email.trim()) {
      setError("Name and email are required");
      return;
    }

    setError("");
    setIsSubmitting(true);

    try {
      const result = await usersApi.create({
        name: name.trim(),
        email: email.trim(),
      });
      setGeneratedKey(result.api_key);
    } catch {
      setError("Failed to create account. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleCopy = async () => {
    await navigator.clipboard.writeText(generatedKey);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleContinue = () => {
    login(generatedKey);
    router.replace("/onboarding");
  };

  if (generatedKey) {
    return (
      <Card.Root bg="white" shadow="sm" borderRadius="lg">
        <Card.Body p={8}>
          <Heading size="lg" mb={2}>
            Account created!
          </Heading>
          <Text color="gray.500" mb={6} fontSize="sm">
            Save your API key. You will need it to sign in.
          </Text>

          <Box
            bg="gray.100"
            borderRadius="md"
            p={4}
            mb={6}
            border="1px solid"
            borderColor="gray.200"
          >
            <Text fontSize="xs" fontWeight="medium" color="gray.500" mb={2}>
              Your API Key
            </Text>
            <Flex align="center" gap={2}>
              <Text
                fontSize="sm"
                fontFamily="mono"
                flex={1}
                wordBreak="break-all"
              >
                {generatedKey}
              </Text>
              <IconButton
                aria-label="Copy API key"
                size="sm"
                variant="ghost"
                onClick={handleCopy}
              >
                {copied ? <LuCheck /> : <LuCopy />}
              </IconButton>
            </Flex>
          </Box>

          <Button
            w="100%"
            bg="brand.500"
            color="white"
            onClick={handleContinue}
          >
            Continue to setup
          </Button>
        </Card.Body>
      </Card.Root>
    );
  }

  return (
    <Card.Root bg="white" shadow="sm" borderRadius="lg">
      <Card.Body p={8}>
        <form onSubmit={handleSubmit}>
          <Heading size="lg" mb={2}>
            Create your account
          </Heading>
          <Text color="gray.500" mb={6} fontSize="sm">
            Get started with SCOUT
          </Text>

          <Box mb={4}>
            <Text fontSize="sm" fontWeight="medium" mb={1}>
              Name
            </Text>
            <Input
              placeholder="Your name"
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
          </Box>

          <Box mb={4}>
            <Text fontSize="sm" fontWeight="medium" mb={1}>
              Email
            </Text>
            <Input
              type="email"
              placeholder="you@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
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
            Create Account
          </Button>

          <Text fontSize="sm" textAlign="center" color="gray.500">
            Already have an account?{" "}
            <Link href="/login" style={{ color: "#1a1a2e", fontWeight: 600 }}>
              Sign in
            </Link>
          </Text>
        </form>
      </Card.Body>
    </Card.Root>
  );
}
