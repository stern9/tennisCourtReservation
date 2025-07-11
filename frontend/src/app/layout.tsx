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
  title: "Tennis Court Reservation System",
  description: "Automated tennis court booking and reservation management system",
  keywords: ["tennis", "court", "reservation", "booking", "automation"],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased min-h-screen bg-background text-foreground`}
      >
        <div className="flex flex-col min-h-screen">
          <header className="border-b border-border">
            <div className="container mx-auto px-4 py-4">
              <h1 className="text-2xl font-bold text-court-green">
                🎾 Tennis Court Reservation
              </h1>
              <p className="text-sm text-muted-foreground">
                Automated booking and management system
              </p>
            </div>
          </header>
          
          <main className="flex-1 container mx-auto px-4 py-8">
            {children}
          </main>
          
          <footer className="border-t border-border mt-auto">
            <div className="container mx-auto px-4 py-4 text-center text-sm text-muted-foreground">
              <p>&copy; 2024 Tennis Court Reservation System. Built with Next.js & FastAPI.</p>
            </div>
          </footer>
        </div>
      </body>
    </html>
  );
}
