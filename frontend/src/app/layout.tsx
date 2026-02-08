import type { Metadata } from "next";
import { Inter } from "next/font/google";
import Link from "next/link";
import "./globals.css";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Stock Analyser",
  description: "Analyze stocks based on analyst performance and ratings",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={`${inter.variable} font-sans antialiased bg-gray-50 dark:bg-gray-950 min-h-screen`}>
        {/* Navigation Header */}
        <nav className="sticky top-0 z-50 bg-white/80 dark:bg-gray-900/80 backdrop-blur-md border-b border-gray-200 dark:border-gray-800">
          <div className="container mx-auto px-4">
            <div className="flex items-center justify-between h-16">
              <Link href="/" className="flex items-center gap-2">
                <span className="text-2xl">📈</span>
                <span className="text-xl font-bold bg-gradient-to-r from-blue-600 to-emerald-600 bg-clip-text text-transparent">
                  Stock Analyser
                </span>
              </Link>
              <div className="flex items-center gap-6">
                <Link
                  href="/analysts"
                  className="text-gray-600 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400 font-medium transition-colors"
                >
                  Analysts
                </Link>
                <Link
                  href="/companies"
                  className="text-gray-600 dark:text-gray-300 hover:text-emerald-600 dark:hover:text-emerald-400 font-medium transition-colors"
                >
                  Companies
                </Link>
                <Link
                  href="/admin"
                  className="text-gray-600 dark:text-gray-300 hover:text-purple-600 dark:hover:text-purple-400 font-medium transition-colors"
                >
                  Admin
                </Link>
              </div>
            </div>
          </div>
        </nav>

        {/* Main Content */}
        <main>{children}</main>
      </body>
    </html>
  );
}
