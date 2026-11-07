import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "PRAESYNC / HUD - Stateless Cluster Telemetry",
  description: "Real-time operations terminal and telemetry HUD for praesync-core",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="h-full bg-canvas text-slate-200 antialiased">
      <body className="min-h-full flex flex-col bg-canvas text-slate-200 selection:bg-accent selection:text-canvas">
        {children}
      </body>
    </html>
  );
}
