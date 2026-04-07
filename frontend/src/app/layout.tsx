import type { Metadata } from "next";
import { Providers } from "@/providers/Providers";

export const metadata: Metadata = {
  title: "SCOUT",
  description: "Podcast post-production dashboard",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body style={{ margin: 0, fontFamily: "Inter, system-ui, sans-serif" }}>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
