import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "UhakikiAI - Sovereign Identity Verification System",
  description: "Advanced AI-powered identity verification and fraud prevention for Kenya's education sector. Real-time document forgery detection, biometric authentication, and autonomous fraud investigation.",
  keywords: "identity verification, fraud detection, AI, biometrics, Kenya education, document security",
  authors: [{ name: "UhakikiAI Team" }],
  creator: "UhakikiAI",
  publisher: "UhakikiAI",
  formatDetection: {
    email: false,
    address: false,
    telephone: false,
  },
  openGraph: {
    title: "UhakikiAI - Sovereign Identity Verification System",
    description: "Advanced AI-powered identity verification and fraud prevention for Kenya's education sector",
    url: "https://uhakiki.ai",
    siteName: "UhakikiAI",
    locale: "en_KE",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "UhakikiAI - Sovereign Identity Verification System",
    description: "Advanced AI-powered identity verification and fraud prevention for Kenya's education sector",
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      "max-video-preview": -1,
      "max-image-preview": "large",
      "max-snippet": -1,
    },
  },
  verification: {
    google: "your-google-verification-code",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en-KE">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        {children}
      </body>
    </html>
  );
}
