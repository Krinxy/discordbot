import type { Metadata } from "next";
import { Geist_Mono } from "next/font/google";
import Link from "next/link";

import { ThemeProvider } from "@/components/theme-provider";
import { ThemeToggle } from "@/components/theme-toggle";
import { TooltipProvider } from "@/components/ui/tooltip";
import { Toaster } from "@/components/ui/sonner";
import { VitalsStrip } from "@/components/vitals-strip";

import "./globals.css";

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Mois D Zois — Admin",
  description: "Admin dashboard for the Mois D Zois Discord bot's services.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      suppressHydrationWarning
      className={`${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col bg-background text-foreground">
        <ThemeProvider attribute="class" defaultTheme="dark" enableSystem={false} disableTransitionOnChange>
          <TooltipProvider delay={150}>
            <header className="sticky top-0 z-10 border-b border-border/60 bg-background/80 backdrop-blur-md">
              <div className="mx-auto flex max-w-5xl items-center justify-between gap-4 px-6 py-3">
                <Link href="/" className="flex items-baseline gap-2">
                  <span className="font-heading text-sm font-semibold tracking-tight">MOIS D ZOIS</span>
                  <span className="text-xs font-normal text-muted-foreground">admin</span>
                </Link>
                <div className="hidden sm:block">
                  <VitalsStrip />
                </div>
                <ThemeToggle />
              </div>
            </header>
            <main className="mx-auto w-full max-w-5xl flex-1 px-6 py-10">{children}</main>
            <Toaster />
          </TooltipProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
