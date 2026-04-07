export const queryKeys = {
  user: ["user"] as const,
  profile: ["profile"] as const,
  jobs: {
    all: ["jobs"] as const,
    list: (params: Record<string, unknown>) => ["jobs", "list", params] as const,
    detail: (id: string) => ["jobs", "detail", id] as const,
  },
  clips: {
    all: ["clips"] as const,
    list: (params: Record<string, unknown>) => ["clips", "list", params] as const,
    detail: (id: string) => ["clips", "detail", id] as const,
  },
  social: ["social-accounts"] as const,
  analytics: {
    reports: (params: Record<string, unknown>) =>
      ["analytics", "reports", params] as const,
    report: (id: string) => ["analytics", "reports", id] as const,
  },
};
