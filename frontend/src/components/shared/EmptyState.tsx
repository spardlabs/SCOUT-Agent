"use client";

import { Flex, Heading, Text, Box } from "@chakra-ui/react";
import { ReactElement, ReactNode } from "react";

interface EmptyStateProps {
  icon: ReactElement;
  title: string;
  description: string;
  action?: ReactNode;
}

export function EmptyState({ icon, title, description, action }: EmptyStateProps) {
  return (
    <Flex direction="column" align="center" justify="center" py={12} gap={4}>
      <Box color="gray.400" fontSize="4xl">
        {icon}
      </Box>
      <Heading size="md">{title}</Heading>
      <Text color="gray.600" textAlign="center" maxW="sm">
        {description}
      </Text>
      {action && <Box mt={2}>{action}</Box>}
    </Flex>
  );
}
