"use client";

import { Heading, SimpleGrid, Box } from "@chakra-ui/react";
import { LuFileAudio, LuFilm, LuCircleCheck, LuClock } from "react-icons/lu";
import { KpiStatCard } from "@/components/dashboard/KpiStatCard";
import { RecentJobsList } from "@/components/dashboard/RecentJobsList";
import { QuickActions } from "@/components/dashboard/QuickActions";
import { useJobs } from "@/hooks/useJobs";
import { useClips } from "@/hooks/useClips";

export default function DashboardPage() {
  const { data: jobsData } = useJobs();
  const { data: clipsData } = useClips();

  const totalJobs = jobsData?.total ?? 0;
  const totalClips = clipsData?.total ?? 0;
  const completedJobs =
    jobsData?.jobs.filter((j) => j.status === "complete").length ?? 0;
  const pendingJobs =
    jobsData?.jobs.filter((j) => j.status === "pending").length ?? 0;

  return (
    <Box>
      <Heading size="lg" mb={6}>
        Dashboard
      </Heading>

      <SimpleGrid columns={{ base: 1, md: 2, lg: 4 }} gap={4} mb={8}>
        <KpiStatCard
          label="Total Jobs"
          value={totalJobs}
          helpText="All time"
          icon={<LuFileAudio />}
        />
        <KpiStatCard
          label="Total Clips"
          value={totalClips}
          helpText="Generated"
          icon={<LuFilm />}
        />
        <KpiStatCard
          label="Completed"
          value={completedJobs}
          helpText="Jobs finished"
          icon={<LuCircleCheck />}
        />
        <KpiStatCard
          label="Pending"
          value={pendingJobs}
          helpText="In queue"
          icon={<LuClock />}
        />
      </SimpleGrid>

      <SimpleGrid columns={{ base: 1, md: 2 }} gap={6}>
        <RecentJobsList />
        <QuickActions />
      </SimpleGrid>
    </Box>
  );
}
