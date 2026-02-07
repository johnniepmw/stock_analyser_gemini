import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";

export default function HomePage() {
  return (
    <div className="container mx-auto py-12 px-4">
      {/* Hero Section */}
      <div className="text-center mb-12">
        <h1 className="text-5xl font-bold mb-4 bg-gradient-to-r from-blue-600 via-purple-600 to-emerald-600 bg-clip-text text-transparent">
          Stock Analyser
        </h1>
        <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
          Make smarter investment decisions by evaluating analysts based on their
          track record, then using their weighted ratings to identify high-potential stocks.
        </p>
      </div>

      {/* Feature Cards */}
      <div className="grid md:grid-cols-2 gap-8 max-w-4xl mx-auto">
        <Link href="/analysts" className="group">
          <Card className="h-full transition-all duration-300 hover:shadow-xl hover:-translate-y-1 border-2 hover:border-blue-500/50">
            <CardHeader>
              <div className="text-5xl mb-4">👨‍💼</div>
              <CardTitle className="text-2xl group-hover:text-blue-600 transition-colors">
                Analysts
              </CardTitle>
              <CardDescription className="text-base">
                Browse analysts ranked by their prediction accuracy. See which firms
                have the best track record and explore their historical ratings.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li className="flex items-center gap-2">
                  <span className="text-emerald-500">✓</span>
                  Confidence scores based on historical accuracy
                </li>
                <li className="flex items-center gap-2">
                  <span className="text-emerald-500">✓</span>
                  Full rating history per analyst
                </li>
                <li className="flex items-center gap-2">
                  <span className="text-emerald-500">✓</span>
                  Sort by performance metrics
                </li>
              </ul>
            </CardContent>
          </Card>
        </Link>

        <Link href="/companies" className="group">
          <Card className="h-full transition-all duration-300 hover:shadow-xl hover:-translate-y-1 border-2 hover:border-emerald-500/50">
            <CardHeader>
              <div className="text-5xl mb-4">🏢</div>
              <CardTitle className="text-2xl group-hover:text-emerald-600 transition-colors">
                Companies
              </CardTitle>
              <CardDescription className="text-base">
                S&P 500 companies ranked by investment potential. Scores are weighted
                by analyst confidence for smarter insights.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li className="flex items-center gap-2">
                  <span className="text-emerald-500">✓</span>
                  Investment scores weighted by analyst accuracy
                </li>
                <li className="flex items-center gap-2">
                  <span className="text-emerald-500">✓</span>
                  Target prices with upside potential
                </li>
                <li className="flex items-center gap-2">
                  <span className="text-emerald-500">✓</span>
                  Filter by sector
                </li>
              </ul>
            </CardContent>
          </Card>
        </Link>
      </div>

      {/* How It Works */}
      <div className="mt-16 max-w-4xl mx-auto">
        <h2 className="text-2xl font-bold text-center mb-8">How It Works</h2>
        <div className="grid md:grid-cols-3 gap-6">
          <div className="text-center p-6 bg-gradient-to-br from-blue-500/5 to-purple-500/5 rounded-xl">
            <div className="text-3xl mb-3">1️⃣</div>
            <h3 className="font-semibold mb-2">Ingest Data</h3>
            <p className="text-sm text-muted-foreground">
              Historical stock prices and analyst ratings are collected from multiple sources
            </p>
          </div>
          <div className="text-center p-6 bg-gradient-to-br from-purple-500/5 to-pink-500/5 rounded-xl">
            <div className="text-3xl mb-3">2️⃣</div>
            <h3 className="font-semibold mb-2">Rank Analysts</h3>
            <p className="text-sm text-muted-foreground">
              Each analyst is scored based on how accurate their past predictions were
            </p>
          </div>
          <div className="text-center p-6 bg-gradient-to-br from-emerald-500/5 to-teal-500/5 rounded-xl">
            <div className="text-3xl mb-3">3️⃣</div>
            <h3 className="font-semibold mb-2">Score Companies</h3>
            <p className="text-sm text-muted-foreground">
              Company ratings are weighted by analyst confidence for better insights
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
