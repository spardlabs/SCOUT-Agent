"use client";

import { Card, Heading, Stack, Button } from "@chakra-ui/react";
import Link from "next/link";

export function QuickActions() {
  return (
    <Card.Root shadow="sm" height="100%">
      <Card.Header>
        <Heading size="sm">Quick Actions</Heading>
      </Card.Header>
      <Card.Body>
        <Stack gap={3}>
          <Button asChild variant="outline" width="100%">
            <Link href="/jobs">View Jobs</Link>
          </Button>
          <Button asChild variant="outline" width="100%">
            <Link href="/clips">View Clips</Link>
          </Button>
          <Button asChild variant="outline" width="100%">
            <Link href="/settings">Edit Profile</Link>
          </Button>
        </Stack>
      </Card.Body>
    </Card.Root>
  );
}
