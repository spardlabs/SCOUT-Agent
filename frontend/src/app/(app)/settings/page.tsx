"use client";

import { useState, useEffect } from "react";
import {
  Box, Heading, Card, Text, Flex, Button, Input, SimpleGrid, VStack,
  Tabs, Badge, Textarea,
} from "@chakra-ui/react";
import { useProfile, useUpdateProfile } from "@/hooks/useProfile";
import { useAuth } from "@/providers/AuthProvider";
import { LoadingSkeleton } from "@/components/shared/LoadingSkeleton";

const EDITING_STYLES = ["tight", "conversational", "cinematic"];
const ALL_PLATFORMS = ["tiktok", "instagram", "youtube_shorts", "twitter", "linkedin"];

export default function SettingsPage() {
  const { user, apiKey } = useAuth();
  const { data: profile, isLoading } = useProfile();
  const updateProfile = useUpdateProfile();

  const [form, setForm] = useState({
    silence_threshold_ms: 1500,
    target_lufs: -16.0,
    editing_style: "conversational",
    brand_color_primary: "#1a1a2e",
    brand_color_secondary: "#e94560",
    brand_font: "Montserrat-Bold",
    topics: "",
    humor: 0.5,
    controversy: 0.2,
    education: 0.7,
    target_platforms: ["tiktok", "instagram", "youtube_shorts"] as string[],
    clip_min: 30,
    clip_max: 90,
  });
  const [showKey, setShowKey] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    if (profile) {
      setForm({
        silence_threshold_ms: profile.silence_threshold_ms,
        target_lufs: profile.target_lufs,
        editing_style: profile.editing_style,
        brand_color_primary: profile.brand_color_primary,
        brand_color_secondary: profile.brand_color_secondary,
        brand_font: profile.brand_font,
        topics: (profile.topics || []).join(", "),
        humor: profile.virality_preferences?.humor ?? 0.5,
        controversy: profile.virality_preferences?.controversy ?? 0.2,
        education: profile.virality_preferences?.education ?? 0.7,
        target_platforms: profile.target_platforms || [],
        clip_min: profile.clip_length_range?.min_seconds ?? 30,
        clip_max: profile.clip_length_range?.max_seconds ?? 90,
      });
    }
  }, [profile]);

  const handleSave = () => {
    updateProfile.mutate(
      {
        silence_threshold_ms: form.silence_threshold_ms,
        target_lufs: form.target_lufs,
        editing_style: form.editing_style,
        brand_color_primary: form.brand_color_primary,
        brand_color_secondary: form.brand_color_secondary,
        brand_font: form.brand_font,
        topics: form.topics.split(",").map((t) => t.trim()).filter(Boolean),
        virality_preferences: {
          humor: form.humor,
          controversy: form.controversy,
          education: form.education,
        },
        target_platforms: form.target_platforms,
        clip_length_range: { min_seconds: form.clip_min, max_seconds: form.clip_max },
      },
      { onSuccess: () => { setSaved(true); setTimeout(() => setSaved(false), 2000); } },
    );
  };

  if (isLoading) return <LoadingSkeleton variant="detail" />;

  return (
    <Box>
      <Heading size="lg" mb={6}>Settings</Heading>

      <Tabs.Root defaultValue="profile">
        <Tabs.List mb={4}>
          <Tabs.Trigger value="profile">Editing Profile</Tabs.Trigger>
          <Tabs.Trigger value="account">Account</Tabs.Trigger>
        </Tabs.List>

        <Tabs.Content value="profile">
          <VStack gap={6} align="stretch" maxW="700px">
            {/* Audio Settings */}
            <Card.Root>
              <Card.Body>
                <Heading size="sm" mb={4}>Audio Settings</Heading>
                <SimpleGrid columns={{ base: 1, md: 3 }} gap={4}>
                  <Box>
                    <Text fontSize="sm" mb={1}>Silence Threshold (ms)</Text>
                    <Input
                      type="number"
                      value={form.silence_threshold_ms}
                      onChange={(e) => setForm({ ...form, silence_threshold_ms: Number(e.target.value) })}
                    />
                  </Box>
                  <Box>
                    <Text fontSize="sm" mb={1}>Target LUFS</Text>
                    <Input
                      type="number"
                      step={0.5}
                      value={form.target_lufs}
                      onChange={(e) => setForm({ ...form, target_lufs: Number(e.target.value) })}
                    />
                  </Box>
                  <Box>
                    <Text fontSize="sm" mb={1}>Editing Style</Text>
                    <select
                      value={form.editing_style}
                      onChange={(e) => setForm({ ...form, editing_style: e.target.value })}
                      style={{
                        width: "100%", padding: "8px 12px", borderRadius: "6px",
                        border: "1px solid #E2E8F0", fontSize: "14px",
                      }}
                    >
                      {EDITING_STYLES.map((s) => (
                        <option key={s} value={s}>{s.charAt(0).toUpperCase() + s.slice(1)}</option>
                      ))}
                    </select>
                  </Box>
                </SimpleGrid>
              </Card.Body>
            </Card.Root>

            {/* Branding */}
            <Card.Root>
              <Card.Body>
                <Heading size="sm" mb={4}>Branding</Heading>
                <SimpleGrid columns={{ base: 1, md: 3 }} gap={4}>
                  <Box>
                    <Text fontSize="sm" mb={1}>Primary Color</Text>
                    <Flex gap={2}>
                      <Input
                        type="color"
                        value={form.brand_color_primary}
                        onChange={(e) => setForm({ ...form, brand_color_primary: e.target.value })}
                        width="50px"
                        p={0}
                      />
                      <Input
                        value={form.brand_color_primary}
                        onChange={(e) => setForm({ ...form, brand_color_primary: e.target.value })}
                        size="sm"
                      />
                    </Flex>
                  </Box>
                  <Box>
                    <Text fontSize="sm" mb={1}>Secondary Color</Text>
                    <Flex gap={2}>
                      <Input
                        type="color"
                        value={form.brand_color_secondary}
                        onChange={(e) => setForm({ ...form, brand_color_secondary: e.target.value })}
                        width="50px"
                        p={0}
                      />
                      <Input
                        value={form.brand_color_secondary}
                        onChange={(e) => setForm({ ...form, brand_color_secondary: e.target.value })}
                        size="sm"
                      />
                    </Flex>
                  </Box>
                  <Box>
                    <Text fontSize="sm" mb={1}>Font</Text>
                    <Input
                      value={form.brand_font}
                      onChange={(e) => setForm({ ...form, brand_font: e.target.value })}
                    />
                  </Box>
                </SimpleGrid>
              </Card.Body>
            </Card.Root>

            {/* Content Preferences */}
            <Card.Root>
              <Card.Body>
                <Heading size="sm" mb={4}>Content Preferences</Heading>
                <Box mb={4}>
                  <Text fontSize="sm" mb={1}>Topics (comma-separated)</Text>
                  <Input
                    value={form.topics}
                    onChange={(e) => setForm({ ...form, topics: e.target.value })}
                    placeholder="tech, AI, startups"
                  />
                </Box>
                <SimpleGrid columns={3} gap={4} mb={4}>
                  <Box>
                    <Text fontSize="sm" mb={1}>Humor (0-1)</Text>
                    <Input type="number" step={0.1} min={0} max={1} value={form.humor}
                      onChange={(e) => setForm({ ...form, humor: Number(e.target.value) })} />
                  </Box>
                  <Box>
                    <Text fontSize="sm" mb={1}>Controversy (0-1)</Text>
                    <Input type="number" step={0.1} min={0} max={1} value={form.controversy}
                      onChange={(e) => setForm({ ...form, controversy: Number(e.target.value) })} />
                  </Box>
                  <Box>
                    <Text fontSize="sm" mb={1}>Education (0-1)</Text>
                    <Input type="number" step={0.1} min={0} max={1} value={form.education}
                      onChange={(e) => setForm({ ...form, education: Number(e.target.value) })} />
                  </Box>
                </SimpleGrid>

                <Text fontSize="sm" mb={2}>Target Platforms</Text>
                <Flex gap={2} flexWrap="wrap" mb={4}>
                  {ALL_PLATFORMS.map((p) => (
                    <Badge
                      key={p}
                      cursor="pointer"
                      colorPalette={form.target_platforms.includes(p) ? "blue" : "gray"}
                      onClick={() => {
                        const next = form.target_platforms.includes(p)
                          ? form.target_platforms.filter((x) => x !== p)
                          : [...form.target_platforms, p];
                        setForm({ ...form, target_platforms: next });
                      }}
                      px={3} py={1}
                    >
                      {p}
                    </Badge>
                  ))}
                </Flex>

                <SimpleGrid columns={2} gap={4}>
                  <Box>
                    <Text fontSize="sm" mb={1}>Min Clip Length (sec)</Text>
                    <Input type="number" value={form.clip_min}
                      onChange={(e) => setForm({ ...form, clip_min: Number(e.target.value) })} />
                  </Box>
                  <Box>
                    <Text fontSize="sm" mb={1}>Max Clip Length (sec)</Text>
                    <Input type="number" value={form.clip_max}
                      onChange={(e) => setForm({ ...form, clip_max: Number(e.target.value) })} />
                  </Box>
                </SimpleGrid>
              </Card.Body>
            </Card.Root>

            <Button colorPalette="blue" onClick={handleSave} loading={updateProfile.isPending}>
              {saved ? "Saved!" : "Save Changes"}
            </Button>
          </VStack>
        </Tabs.Content>

        <Tabs.Content value="account">
          <Card.Root maxW="500px">
            <Card.Body>
              <VStack gap={4} align="stretch">
                <Box>
                  <Text fontSize="sm" color="gray.500">Name</Text>
                  <Text fontWeight="medium">{user?.name}</Text>
                </Box>
                <Box>
                  <Text fontSize="sm" color="gray.500">Email</Text>
                  <Text fontWeight="medium">{user?.email}</Text>
                </Box>
                <Box>
                  <Text fontSize="sm" color="gray.500">API Key</Text>
                  <Flex gap={2} align="center">
                    <Text fontFamily="mono" fontSize="sm">
                      {showKey ? apiKey : "sk_scout_••••••••••••••••"}
                    </Text>
                    <Button size="sm" variant="ghost" onClick={() => setShowKey(!showKey)}>
                      {showKey ? "Hide" : "Reveal"}
                    </Button>
                  </Flex>
                </Box>
              </VStack>
            </Card.Body>
          </Card.Root>
        </Tabs.Content>
      </Tabs.Root>
    </Box>
  );
}
