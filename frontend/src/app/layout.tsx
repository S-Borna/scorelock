import type { Metadata } from "next";
import { Inter } from "next/font/google";
import Link from "next/link";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "ScoreLock — Football Analytics",
  description:
    "AI-driven football match predictions, sentiment analysis, and value bet identification.",
  keywords: ["football", "predictions", "analytics", "betting", "xgboost"],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className={`${inter.className} bg-gray-950 text-gray-100 antialiased`}>
        <div className="min-h-screen flex flex-col">
          <Header />
          <main className="flex-1">{children}</main>
          <Footer />
        </div>
      </body>
    </html>
  );
}

function Header() {
  return (
    <header className="border-b border-gray-800 bg-gray-950/80 backdrop-blur-sm sticky top-0 z-50">
      <nav className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-2">
          <span className="text-2xl">⚽</span>
          <span className="text-xl font-bold text-scorelock-400">ScoreLock</span>
        </Link>
        <div className="hidden sm:flex items-center gap-6 text-sm">
          <Link href="/matches" className="hover:text-scorelock-400 transition-colors">
            Matches
          </Link>
          <Link href="/predictions" className="hover:text-scorelock-400 transition-colors">
            Predictions
          </Link>
          <Link href="/value-bets" className="hover:text-scorelock-400 transition-colors">
            Value Bets
          </Link>
          <Link href="/standings" className="hover:text-scorelock-400 transition-colors">
            Standings
          </Link>
        </div>
        <div className="flex items-center gap-3">
          <Link
            href="/login"
            className="text-sm hover:text-scorelock-400 transition-colors"
          >
            Log in
          </Link>
          <Link
            href="/signup"
            className="text-sm bg-scorelock-600 hover:bg-scorelock-700 px-4 py-2 rounded-lg transition-colors"
          >
            Sign up
          </Link>
        </div>
      </nav>
    </header>
  );
}

function Footer() {
  return (
    <footer className="border-t border-gray-800 py-8 mt-auto">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center text-sm text-gray-500">
        <p>© 2026 ScoreLock. Data-driven decision support — not betting advice.</p>
      </div>
    </footer>
  );
}
