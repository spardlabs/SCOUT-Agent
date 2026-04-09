"use client";

import { useState } from "react";
import { Box, Heading, Card, Text, SimpleGrid, Flex, Badge } from "@chakra-ui/react";
import { useQuery } from "@tanstack/react-query";
import { analyticsApi } from "@/lib/api/analytics";
import { queryKeys } from "@/lib/query-keys";
import { LoadingSkeleton } from "@/components/shared/LoadingSkeleton";
import { EmptyState } from "@/components/shared/EmptyState";
import { LuChartBar } from "react-icons/lu";
import type { WeeklyReportResponse } from "@/types/api";

function StatCard({ label, value }: { label: string; value: string | number }) {
  return (
    <Card.Root>
      <Card.Body>
        <Text fontSize="sm" color="gray.500">{label}</Text>
        <Text fontSize="2xl" fontWeight="bold">{value}</Text>
      </Card.Body>
    </Card.Root>
  );
}

export default function AnalyticsPage() {
  const [selectedReportId, setSelectedReportId] = useState<string | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: queryKeys.analytics.reports({}),
    queryFn: () => analyticsApi.listReports({ limit: 20 }),
  });

  const { data: selectedReport } = useQuery({
    queryKey: queryKeys.analytics.report(selectedReportId || ""),
    queryFn: () => analyticsApi.getReport(selectedReportId!),
    enabled: !!selectedReportId,
  });

  if (isLoading) return <LoadingSkeleton variant="cards" />;

  const reports = data?.reports || [];

  if (reports.length === 0) {
    return (
      <Box>
        <Heading size="lg" mb={6}>Analytics</Heading>
        <EmptyState
          icon={<LuChartBar size={32} />}
          title="No reports yet"
          description="Weekly performance reports will appear here once your clips start getting posted."
        />
      </Box>
    );
  }

  const activeReport = selectedReport || reports[0];
  const metrics = (activeReport?.report_data || {}) as Record<string, unknown>;
  const totalMetrics = (metrics.total_metrics || {}) as Record<string, number>;

  return (
    <Box>
      <Heading size="lg" mb={6}>Analytics</Heading>

      <Flex gap={6} direction={{ base: "column", lg: "row" }}>
        {/* Report list */}
        <Box minW="280px">
          <Heading size="sm" mb={3}>Weekly Reports</Heading>
          {reports.map((report) => (
            <Card.Root
              key={report.id}
              mb={2}
              cursor="pointer"
              borderWidth={activeReport?.id === report.id ? "2px" : "1px"}
              borderColor={activeReport?.id === report.id ? "blue.500" : "gray.200"}
              onClick={() => setSelectedReportId(report.id)}
            >
              <Card.Body py={3} px={4}>
                <Text fontWeight="medium" fontSize="sm">
                  {report.week_start} — {report.week_end}
                </Text>
                <Badge
                  colorPalette={report.delivered_at ? "green" : "yellow"}
                  size="sm"
                  mt={1}
                >
                  {report.delivered_at ? "Delivered" : "Pending"}
                </Badge>
              </Card.Body>
            </Card.Root>
          ))}
        </Box>

        {/* Report detail */}
        <Box flex={1}>
          {activeReport && (
            <>
              <SimpleGrid columns={{ base: 2, md: 4 }} gap={4} mb={6}>
                <StatCard label="Views" value={totalMetrics.views || 0} />
                <StatCard label="Likes" value={totalMetrics.likes || 0} />
                <StatCard label="Comments" value={totalMetrics.comments || 0} />
                <StatCard label="Shares" value={totalMetrics.shares || 0} />
              </SimpleGrid>

              <Card.Root>
                <Card.Body>
                  <Heading size="sm" mb={3}>AI Insights</Heading>
                  <Text whiteSpace="pre-wrap" color="gray.700" lineHeight="tall">
                    {activeReport.narrative}
                  </Text>
                </Card.Body>
              </Card.Root>
            </>
          )}
        </Box>
      </Flex>
    </Box>
  );
}
