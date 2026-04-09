"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import {
  Box, Heading, Text, Button, Card, Input, SimpleGrid, Flex, Badge, VStack,
} from "@chakra-ui/react";
import { profilesApi } from "@/lib/api/profiles";
import { LuArrowRight, LuArrowLeft, LuCheck } from "react-icons/lu";

const STEPS = ["Welcome", "Editing", "Branding", "Finish"];
const EDITING_STYLES = ["tight", "conversational", "cinematic"];
const ALL_PLATFORMS = ["tiktok", "instagram", "youtube_shorts", "twitter", "linkedin"];

export default function OnboardingPage() {
  const router = useRouter();
  const [step, setStep] = useState(0);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState({
    silence_threshold_ms: 1500,
    target_lufs: -16.0,
    editing_style: "conversational",
    brand_color_primary: "#1a1a2e",
    brand_color_secondary: "#e94560",
    brand_font: "Montserrat-Bold",
    topics: "",
    target_platforms: ["tiktok", "instagram", "youtube_shorts"] as string[],
  });

  const handleFinish = async () => {
    setSaving(true);
    try {
      await profilesApi.create({
        silence_threshold_ms: form.silence_threshold_ms,
        target_lufs: form.target_lufs,
        editing_style: form.editing_style,
        brand_color_primary: form.brand_color_primary,
        brand_color_secondary: form.brand_color_secondary,
        brand_font: form.brand_font,
        topics: form.topics.split(",").map((t) => t.trim()).filter(Boolean),
        target_platforms: form.target_platforms,
      });
      router.push("/dashboard");
    } catch {
      setSaving(false);
    }
  };

  return (
    <Flex minH="100vh" bg="gray.50" align="center" justify="center" p={4}>
      <Box maxW="600px" w="100%">
        {/* Step Indicator */}
        <Flex justify="center" gap={2} mb={8}>
          {STEPS.map((label, i) => (
            <Flex key={label} align="center" gap={2}>
              <Flex
                w="32px" h="32px" borderRadius="full" align="center" justify="center"
                bg={i <= step ? "blue.500" : "gray.200"}
                color={i <= step ? "white" : "gray.500"}
                fontSize="sm" fontWeight="bold"
              >
                {i < step ? <LuCheck size={14} /> : i + 1}
              </Flex>
              <Text fontSize="sm" color={i <= step ? "gray.800" : "gray.400"} display={{ base: "none", md: "block" }}>
                {label}
              </Text>
              {i < STEPS.length - 1 && <Box w="40px" h="2px" bg={i < step ? "blue.500" : "gray.200"} />}
            </Flex>
          ))}
        </Flex>

        <Card.Root>
          <Card.Body p={8}>
            {/* Step 0: Welcome */}
            {step === 0 && (
              <VStack gap={4} textAlign="center">
                <Heading size="xl">Welcome to SCOUT</Heading>
                <Text color="gray.600" fontSize="lg" maxW="400px">
                  Let's set up your podcast editing profile. This takes about 2 minutes
                  and helps our AI agents edit your content exactly how you want it.
                </Text>
                <Button colorPalette="blue" size="lg" onClick={() => setStep(1)}>
                  Get Started <LuArrowRight />
                </Button>
              </VStack>
            )}

            {/* Step 1: Editing Preferences */}
            {step === 1 && (
              <VStack gap={5} align="stretch">
                <Heading size="lg">Editing Preferences</Heading>
                <Text color="gray.500">How should we edit your episodes?</Text>

                <Box>
                  <Text fontSize="sm" mb={1} fontWeight="medium">Silence Threshold (ms)</Text>
                  <Text fontSize="xs" color="gray.400" mb={2}>Silences longer than this get removed</Text>
                  <Input type="number" value={form.silence_threshold_ms}
                    onChange={(e) => setForm({ ...form, silence_threshold_ms: Number(e.target.value) })} />
                </Box>

                <Box>
                  <Text fontSize="sm" mb={1} fontWeight="medium">Target LUFS</Text>
                  <Text fontSize="xs" color="gray.400" mb={2}>Audio loudness level (-16 is standard)</Text>
                  <Input type="number" step={0.5} value={form.target_lufs}
                    onChange={(e) => setForm({ ...form, target_lufs: Number(e.target.value) })} />
                </Box>

                <Box>
                  <Text fontSize="sm" mb={1} fontWeight="medium">Editing Style</Text>
                  <Flex gap={2}>
                    {EDITING_STYLES.map((s) => (
                      <Badge key={s} cursor="pointer" px={4} py={2} borderRadius="full"
                        colorPalette={form.editing_style === s ? "blue" : "gray"}
                        onClick={() => setForm({ ...form, editing_style: s })}
                      >
                        {s.charAt(0).toUpperCase() + s.slice(1)}
                      </Badge>
                    ))}
                  </Flex>
                </Box>

                <Box>
                  <Text fontSize="sm" mb={1} fontWeight="medium">Topics</Text>
                  <Input placeholder="tech, AI, startups" value={form.topics}
                    onChange={(e) => setForm({ ...form, topics: e.target.value })} />
                </Box>
              </VStack>
            )}

            {/* Step 2: Branding */}
            {step === 2 && (
              <VStack gap={5} align="stretch">
                <Heading size="lg">Branding</Heading>
                <Text color="gray.500">Set your visual identity for clips.</Text>

                <SimpleGrid columns={2} gap={4}>
                  <Box>
                    <Text fontSize="sm" mb={1} fontWeight="medium">Primary Color</Text>
                    <Flex gap={2}>
                      <Input type="color" value={form.brand_color_primary} width="50px" p={0}
                        onChange={(e) => setForm({ ...form, brand_color_primary: e.target.value })} />
                      <Input value={form.brand_color_primary}
                        onChange={(e) => setForm({ ...form, brand_color_primary: e.target.value })} />
                    </Flex>
                  </Box>
                  <Box>
                    <Text fontSize="sm" mb={1} fontWeight="medium">Secondary Color</Text>
                    <Flex gap={2}>
                      <Input type="color" value={form.brand_color_secondary} width="50px" p={0}
                        onChange={(e) => setForm({ ...form, brand_color_secondary: e.target.value })} />
                      <Input value={form.brand_color_secondary}
                        onChange={(e) => setForm({ ...form, brand_color_secondary: e.target.value })} />
                    </Flex>
                  </Box>
                </SimpleGrid>

                <Box>
                  <Text fontSize="sm" mb={1} fontWeight="medium">Font</Text>
                  <Input value={form.brand_font}
                    onChange={(e) => setForm({ ...form, brand_font: e.target.value })} />
                </Box>

                <Box>
                  <Text fontSize="sm" mb={1} fontWeight="medium">Target Platforms</Text>
                  <Flex gap={2} flexWrap="wrap">
                    {ALL_PLATFORMS.map((p) => (
                      <Badge key={p} cursor="pointer" px={3} py={1}
                        colorPalette={form.target_platforms.includes(p) ? "blue" : "gray"}
                        onClick={() => {
                          const next = form.target_platforms.includes(p)
                            ? form.target_platforms.filter((x) => x !== p)
                            : [...form.target_platforms, p];
                          setForm({ ...form, target_platforms: next });
                        }}
                      >
                        {p}
                      </Badge>
                    ))}
                  </Flex>
                </Box>
              </VStack>
            )}

            {/* Step 3: Finish */}
            {step === 3 && (
              <VStack gap={4} textAlign="center">
                <Heading size="lg">You're all set!</Heading>
                <Text color="gray.600">
                  Your editing profile is ready. Upload your first episode and our AI agents
                  will handle the rest - editing, clipping, and posting.
                </Text>
                <Button colorPalette="blue" size="lg" onClick={handleFinish} loading={saving}>
                  Go to Dashboard <LuArrowRight />
                </Button>
              </VStack>
            )}

            {/* Navigation */}
            {step > 0 && step < 3 && (
              <Flex justify="space-between" mt={8}>
                <Button variant="ghost" onClick={() => setStep(step - 1)}>
                  <LuArrowLeft /> Back
                </Button>
                <Button colorPalette="blue" onClick={() => setStep(step + 1)}>
                  Continue <LuArrowRight />
                </Button>
              </Flex>
            )}
          </Card.Body>
        </Card.Root>
      </Box>
    </Flex>
  );
}
