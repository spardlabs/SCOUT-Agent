"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { Box, Flex, Skeleton } from "@chakra-ui/react";
import { useAuth } from "@/providers/AuthProvider";
import { Sidebar } from "@/components/layout/Sidebar";
import { TopBar } from "@/components/layout/TopBar";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.replace("/login");
    }
  }, [isAuthenticated, isLoading, router]);

  if (isLoading) {
    return (
      <Flex minH="100vh" p={8} direction="column" gap={4}>
        <Skeleton height="40px" />
        <Skeleton height="200px" />
        <Skeleton height="200px" />
      </Flex>
    );
  }

  if (!isAuthenticated) {
    return null;
  }

  return (
    <Flex minH="100vh">
      <Sidebar />
      <Box flex={1} ml="240px">
        <TopBar />
        <Box as="main" p={6} bg="gray.50" minH="calc(100vh - 64px)">
          {children}
        </Box>
      </Box>
    </Flex>
  );
}
