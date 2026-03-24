import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Smart English Test-Prep",
  description: "AI-powered adaptive learning for Vietnamese students",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
