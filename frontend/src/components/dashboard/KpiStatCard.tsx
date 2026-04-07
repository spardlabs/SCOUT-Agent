"use client";

import { Box, Card, Stat } from "@chakra-ui/react";
import { ReactElement } from "react";

interface KpiStatCardProps {
  label: string;
  value: string | number;
  helpText?: string;
  icon: ReactElement;
}

export function KpiStatCard({ label, value, helpText, icon }: KpiStatCardProps) {
  return (
    <Card.Root shadow="sm">
      <Card.Body>
        <Box position="absolute" top={4} right={4} color="gray.400" fontSize="xl">
          {icon}
        </Box>
        <Stat.Root>
          <Stat.Label>{label}</Stat.Label>
          <Stat.ValueText>{value}</Stat.ValueText>
          {helpText && <Stat.HelpText>{helpText}</Stat.HelpText>}
        </Stat.Root>
      </Card.Body>
    </Card.Root>
  );
}
