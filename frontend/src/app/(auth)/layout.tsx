"use client";

import { Box, Flex, Text } from "@chakra-ui/react";
import type { ReactNode } from "react";

export default function AuthLayout({ children }: { children: ReactNode }) {
  return (
    <Flex
      minH="100vh"
      align="center"
      justify="center"
      bg="gray.50"
      direction="column"
      p={4}
    >
      <Text
        fontSize="2xl"
        fontWeight="bold"
        color="brand.500"
        mb={8}
        letterSpacing="wider"
      >
        SCOUT
      </Text>
      <Box w="100%" maxW="440px">
        {children}
      </Box>
    </Flex>
  );
}
