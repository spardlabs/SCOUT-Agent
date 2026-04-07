"use client";

import { Box, Heading, SimpleGrid, Card, Text, Flex, Button, Badge, Input, VStack } from "@chakra-ui/react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { socialApi } from "@/lib/api/social";
import { queryKeys } from "@/lib/query-keys";
import { LoadingSkeleton } from "@/components/shared/LoadingSkeleton";
import { EmptyState } from "@/components/shared/EmptyState";
import { SiTiktok, SiInstagram, SiYoutube } from "react-icons/si";
import { LuShare2, LuTrash2, LuX, LuBriefcase } from "react-icons/lu";
import { useState } from "react";
import type { Platform } from "@/types/api";

const PLATFORMS: { key: Platform; label: string; icon: React.ReactElement }[] = [
  { key: "tiktok", label: "TikTok", icon: <SiTiktok /> },
  { key: "instagram", label: "Instagram", icon: <SiInstagram /> },
  { key: "youtube", label: "YouTube", icon: <SiYoutube /> },
  { key: "twitter", label: "X / Twitter", icon: <LuX /> },
  { key: "linkedin", label: "LinkedIn", icon: <LuBriefcase /> },
];

export default function SocialPage() {
  const queryClient = useQueryClient();
  const [connectingPlatform, setConnectingPlatform] = useState<Platform | null>(null);
  const [formData, setFormData] = useState({ username: "", token: "" });

  const { data: accounts, isLoading } = useQuery({
    queryKey: queryKeys.social,
    queryFn: socialApi.list,
  });

  const disconnectMutation = useMutation({
    mutationFn: socialApi.disconnect,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.social }),
  });

  const connectMutation = useMutation({
    mutationFn: socialApi.connect,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.social });
      setConnectingPlatform(null);
      setFormData({ username: "", token: "" });
    },
  });

  if (isLoading) return <LoadingSkeleton variant="cards" />;

  const connectedPlatforms = new Set(accounts?.map((a) => a.platform));

  return (
    <Box>
      <Heading size="lg" mb={6}>Social Accounts</Heading>

      {accounts && accounts.length > 0 ? (
        <SimpleGrid columns={{ base: 1, md: 2, lg: 3 }} gap={4} mb={8}>
          {accounts.map((account) => {
            const platform = PLATFORMS.find((p) => p.key === account.platform);
            return (
              <Card.Root key={account.id}>
                <Card.Body>
                  <Flex align="center" gap={3} mb={3}>
                    <Box fontSize="xl">{platform?.icon}</Box>
                    <Box>
                      <Text fontWeight="bold">{platform?.label}</Text>
                      <Text fontSize="sm" color="gray.500">@{account.platform_username}</Text>
                    </Box>
                  </Flex>
                  <Flex justify="space-between" align="center">
                    <Badge colorPalette={account.is_active ? "green" : "gray"}>
                      {account.is_active ? "Active" : "Inactive"}
                    </Badge>
                    <Button
                      size="sm"
                      variant="ghost"
                      colorPalette="red"
                      onClick={() => disconnectMutation.mutate(account.id)}
                    >
                      <LuTrash2 /> Disconnect
                    </Button>
                  </Flex>
                </Card.Body>
              </Card.Root>
            );
          })}
        </SimpleGrid>
      ) : (
        <Box mb={8}>
          <EmptyState
            icon={<LuShare2 size={32} />}
            title="No accounts connected"
            description="Connect your social media accounts to start posting clips."
          />
        </Box>
      )}

      <Heading size="md" mb={4}>Connect a Platform</Heading>
      <Flex gap={3} flexWrap="wrap">
        {PLATFORMS.filter((p) => !connectedPlatforms.has(p.key)).map((platform) => (
          <Button
            key={platform.key}
            variant="outline"
            onClick={() => setConnectingPlatform(platform.key)}
          >
            {platform.icon}
            <Text ml={2}>{platform.label}</Text>
          </Button>
        ))}
        {connectedPlatforms.size === PLATFORMS.length && (
          <Text color="gray.500">All platforms connected!</Text>
        )}
      </Flex>

      {connectingPlatform && (
        <Card.Root mt={4} maxW="400px">
          <Card.Body>
            <Heading size="sm" mb={3}>
              Connect {PLATFORMS.find((p) => p.key === connectingPlatform)?.label}
            </Heading>
            <VStack gap={3}>
              <Input
                placeholder="Username"
                value={formData.username}
                onChange={(e) => setFormData({ ...formData, username: e.target.value })}
              />
              <Input
                placeholder="Access Token"
                type="password"
                value={formData.token}
                onChange={(e) => setFormData({ ...formData, token: e.target.value })}
              />
              <Flex gap={2} width="100%">
                <Button
                  colorPalette="blue"
                  flex={1}
                  onClick={() =>
                    connectMutation.mutate({
                      platform: connectingPlatform,
                      platform_user_id: formData.username,
                      platform_username: formData.username,
                      access_token: formData.token,
                    })
                  }
                >
                  Connect
                </Button>
                <Button variant="ghost" onClick={() => setConnectingPlatform(null)}>
                  Cancel
                </Button>
              </Flex>
            </VStack>
          </Card.Body>
        </Card.Root>
      )}
    </Box>
  );
}
