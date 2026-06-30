import type { Metadata } from "next";
import { Geist, Geist_Mono, Space_Grotesk } from "next/font/google";
import "./globals.css";
import Providers from "@/components/Provider"
import { RouteProvider } from "@/context/RouteContext"

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

// Departure-board display face — used for times, stop badges, headline numerals
const spaceGrotesk = Space_Grotesk({
  variable: "--font-display",
  subsets: ["latin"],
  weight: ["500", "700"],
});

export const metadata: Metadata = {
  title: "Wayfr — Multimodal Public Transport Planner",
  description: "Plan the fastest, cheapest route across Mumbai's local trains and metro.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body
        className={`${geistSans.variable} ${geistMono.variable} ${spaceGrotesk.variable} antialiased`}
      >
        <Providers>
          <RouteProvider>
            {children}
          </RouteProvider>
        </Providers>
      </body>
    </html>
  );
}