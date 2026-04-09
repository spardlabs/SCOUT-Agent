"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Box, Flex, Text } from "@chakra-ui/react";
import {
  LuLayoutDashboard,
  LuBriefcase,
  LuFilm,
  LuShare2,
  LuChartBarIncreasing,
  LuSettings,
  LuUpload,
} from "react-icons/lu";
import { useAuth } from "@/providers/AuthProvider";
import type { IconType } from "react-icons";

interface NavItem {
  label: string;
  href: string;
  icon: IconType;
}

const navItems: NavItem[] = [
  { label: "Upload", href: "/upload", icon: LuUpload },
  { label: "Dashboard", href: "/dashboard", icon: LuLayoutDashboard },
  { label: "Jobs", href: "/jobs", icon: LuBriefcase },
  { label: "Clips", href: "/clips", icon: LuFilm },
  { label: "Social", href: "/social", icon: LuShare2 },
  { label: "Analytics", href: "/analytics", icon: LuChartBarIncreasing },
  { label: "Settings", href: "/settings", icon: LuSettings },
];

export function Sidebar() {
  const pathname = usePathname();
  const { user } = useAuth();

  return (
    <Box
      as="nav"
      position="fixed"
      left={0}
      top={0}
      bottom={0}
      w="240px"
      bg="white"
      borderRight="1px solid"
      borderColor="gray.200"
      display="flex"
      flexDirection="column"
    >
      <Flex align="center" h="64px" px={6}>
        <Text fontSize="xl" fontWeight="bold" color="brand.500" letterSpacing="wider">
          SCOUT
        </Text>
      </Flex>

      <Flex direction="column" flex={1} px={3} py={2} gap={1}>
        {navItems.map((item) => {
          const isActive = pathname.startsWith(item.href);
          const Icon = item.icon;
          return (
            <Link key={item.href} href={item.href} style={{ textDecoration: "none" }}>
              <Flex
                align="center"
                gap={3}
                px={3}
                py={2}
                borderRadius="md"
                bg={isActive ? "gray.100" : "transparent"}
                color={isActive ? "brand.500" : "gray.600"}
                fontWeight={isActive ? "600" : "400"}
                fontSize="sm"
                _hover={{ bg: "gray.50" }}
                transition="all 0.15s"
              >
                <Icon size={18} />
                <Text>{item.label}</Text>
              </Flex>
            </Link>
          );
        })}
      </Flex>

      {user && (
        <Box px={4} py={4} borderTop="1px solid" borderColor="gray.200">
          <Text fontSize="sm" fontWeight="medium" color="gray.700" truncate>
            {user.name}
          </Text>
          <Text fontSize="xs" color="gray.400" truncate>
            {user.email}
          </Text>
        </Box>
      )}
    </Box>
  );
}
