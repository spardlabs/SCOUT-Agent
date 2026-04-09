"use client";

import { usePathname } from "next/navigation";
import { useRouter } from "next/navigation";
import { Box, Flex, Text, Button } from "@chakra-ui/react";
import { LuLogOut } from "react-icons/lu";
import { useAuth } from "@/providers/AuthProvider";

const pageNames: Record<string, string> = {
  dashboard: "Dashboard",
  jobs: "Jobs",
  clips: "Clips",
  social: "Social",
  analytics: "Analytics",
  settings: "Settings",
  onboarding: "Onboarding",
};

export function TopBar() {
  const pathname = usePathname();
  const router = useRouter();
  const { user, logout } = useAuth();

  const segments = pathname.split("/").filter(Boolean);
  const currentPage = segments[0] || "dashboard";
  const pageName = pageNames[currentPage] || currentPage.charAt(0).toUpperCase() + currentPage.slice(1);

  const firstLetter = user?.name?.charAt(0)?.toUpperCase() || "U";

  const handleLogout = () => {
    logout();
    router.replace("/login");
  };

  return (
    <Flex
      h="64px"
      align="center"
      justify="space-between"
      px={6}
      bg="white"
      borderBottom="1px solid"
      borderColor="gray.200"
    >
      <Flex align="center" gap={2}>
        <Text fontSize="sm" color="gray.400">
          SCOUT
        </Text>
        <Text fontSize="sm" color="gray.400">
          /
        </Text>
        <Text fontSize="sm" fontWeight="medium" color="gray.800">
          {pageName}
        </Text>
      </Flex>

      <Flex align="center" gap={3}>
        <Flex
          align="center"
          justify="center"
          w="32px"
          h="32px"
          borderRadius="full"
          bg="brand.500"
          color="white"
          fontSize="sm"
          fontWeight="bold"
        >
          {firstLetter}
        </Flex>
        <Button
          variant="ghost"
          size="sm"
          onClick={handleLogout}
          color="gray.500"
        >
          <LuLogOut />
        </Button>
      </Flex>
    </Flex>
  );
}
