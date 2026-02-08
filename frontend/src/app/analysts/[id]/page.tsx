"use client";

import { useState, useEffect, useMemo } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { ArrowLeft, ChevronRight, Info } from "lucide-react";
import { fetchAnalyst, AnalystDetail, RatingSummary } from "@/lib/api";

function getRatingBadge(rating: string) {
    const colors: Record<string, string> = {
        strong_buy: "bg-emerald-600",
        buy: "bg-emerald-500",
        hold: "bg-amber-500",
        sell: "bg-red-500",
        strong_sell: "bg-red-600",
    };
    return (
        <Badge className={colors[rating] || "bg-gray-500"}>
            {rating.replace("_", " ").toUpperCase()}
        </Badge>
    );
}

function getAccuracyBadge(wasAccurate: boolean | null) {
    if (wasAccurate === null) return <Badge variant="outline">Pending</Badge>;
    return wasAccurate ? (
        <Badge className="bg-emerald-500">✓ Accurate</Badge>
    ) : (
        <Badge className="bg-red-500">✗ Inaccurate</Badge>
    );
}

interface CompanyStats {
    ticker: string;
    name: string | null;
    ratingsCount: number;
    accurateCount: number;
    accuracy: number;
    firstRating: Date;
    lastRating: Date;
    avgReturn: number | null;
    ratings: RatingSummary[];
}

export default function AnalystDetailPage() {
    const params = useParams();
    const analystId = params.id as string;
    const [analyst, setAnalyst] = useState<AnalystDetail | null>(null);
    const [loading, setLoading] = useState(true);
    const [groupByCompany, setGroupByCompany] = useState(false);
    const [selectedCompany, setSelectedCompany] = useState<string | null>(null);

    useEffect(() => {
        fetchAnalyst(analystId)
            .then(setAnalyst)
            .finally(() => setLoading(false));
    }, [analystId]);

    // Cleanup selection when toggling group view
    useEffect(() => {
        if (!groupByCompany) {
            setSelectedCompany(null);
        }
    }, [groupByCompany]);

    const companyStats = useMemo(() => {
        if (!analyst) return [];
        const stats: Record<string, CompanyStats> = {};

        analyst.ratings.forEach((rating) => {
            if (!stats[rating.ticker]) {
                stats[rating.ticker] = {
                    ticker: rating.ticker,
                    name: rating.company_name,
                    ratingsCount: 0,
                    accurateCount: 0,
                    accuracy: 0,
                    firstRating: new Date(rating.date),
                    lastRating: new Date(rating.date),
                    avgReturn: 0,
                    ratings: [],
                };
            }
            const stat = stats[rating.ticker];
            stat.ratingsCount++;
            if (rating.was_accurate) stat.accurateCount++;
            stat.ratings.push(rating);

            const ratingDate = new Date(rating.date);
            if (ratingDate < stat.firstRating) stat.firstRating = ratingDate;
            if (ratingDate > stat.lastRating) stat.lastRating = ratingDate;

            // Only count return if available
            // Note: simple average of returns might be misleading if positions overlap, but sufficient for overview
            // stat.avgReturn logic could be added here if needed
        });

        return Object.values(stats).map((stat) => ({
            ...stat,
            accuracy: (stat.accurateCount / stat.ratingsCount) * 100,
        })).sort((a, b) => b.ratingsCount - a.ratingsCount); // Sort by most rated
    }, [analyst]);

    if (loading) {
        return (
            <div className="flex justify-center items-center min-h-screen">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            </div>
        );
    }

    if (!analyst) {
        return (
            <div className="container mx-auto py-8 px-4">
                <Card>
                    <CardContent className="py-12 text-center">
                        <p className="text-muted-foreground">Analyst not found</p>
                    </CardContent>
                </Card>
            </div>
        );
    }

    const accuracyRate =
        analyst.total_ratings > 0
            ? ((analyst.accurate_ratings / analyst.total_ratings) * 100).toFixed(1)
            : "N/A";

    const selectedCompanyStats = selectedCompany
        ? companyStats.find((c) => c.ticker === selectedCompany)
        : null;

    return (
        <div className="container mx-auto py-8 px-4 space-y-6">
            {/* Header Card */}
            <Card>
                <CardHeader>
                    <div className="flex items-center gap-4">
                        <Link href="/analysts" className="text-blue-600 hover:underline text-sm flex items-center">
                            <ArrowLeft className="h-4 w-4 mr-1" /> Back to Analysts
                        </Link>
                    </div>
                    <CardTitle className="text-3xl font-bold mt-2">{analyst.name}</CardTitle>
                    <CardDescription className="text-lg">{analyst.firm}</CardDescription>
                </CardHeader>
                <CardContent>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div className="bg-gradient-to-br from-blue-500/10 to-purple-500/10 rounded-lg p-4">
                            <p className="text-sm text-muted-foreground">Confidence Score</p>
                            <p className="text-2xl font-bold text-blue-600">
                                {analyst.confidence_score?.toFixed(1) || "N/A"}%
                            </p>
                        </div>
                        <div className="bg-gradient-to-br from-emerald-500/10 to-teal-500/10 rounded-lg p-4">
                            <p className="text-sm text-muted-foreground">Overall Accuracy</p>
                            <p className="text-2xl font-bold text-emerald-600">{accuracyRate}%</p>
                        </div>
                        <div className="bg-gradient-to-br from-amber-500/10 to-orange-500/10 rounded-lg p-4">
                            <p className="text-sm text-muted-foreground">Total Ratings</p>
                            <p className="text-2xl font-bold text-amber-600">{analyst.total_ratings}</p>
                        </div>
                        <div className="bg-gradient-to-br from-pink-500/10 to-rose-500/10 rounded-lg p-4">
                            <p className="text-sm text-muted-foreground">Accurate Calls</p>
                            <p className="text-2xl font-bold text-pink-600">{analyst.accurate_ratings}</p>
                        </div>
                    </div>
                </CardContent>
            </Card>

            {/* View Controls */}
            <div className="flex items-center space-x-2 bg-secondary/20 p-4 rounded-lg border">
                <Switch
                    id="group-view"
                    checked={groupByCompany}
                    onCheckedChange={setGroupByCompany}
                />
                <Label htmlFor="group-view" className="font-medium cursor-pointer">
                    Group ratings by company
                </Label>
            </div>

            {/* Content Area */}
            {selectedCompanyStats ? (
                // Company Detail View
                <Card>
                    <CardHeader>
                        <div className="flex items-center justify-between">
                            <div>
                                <div className="flex items-center gap-2 mb-2">
                                    <Button
                                        variant="ghost"
                                        size="sm"
                                        className="h-8 px-2"
                                        onClick={() => setSelectedCompany(null)}
                                    >
                                        <ArrowLeft className="h-4 w-4 mr-1" />
                                        Back to Overview
                                    </Button>
                                </div>
                                <CardTitle className="text-2xl">
                                    Performance on {selectedCompanyStats.name || selectedCompanyStats.ticker}
                                </CardTitle>
                                <CardDescription>
                                    Analysis of ratings for {selectedCompanyStats.name} ({selectedCompanyStats.ticker})
                                </CardDescription>
                            </div>
                            <div className="text-right">
                                <div className="text-3xl font-bold text-emerald-600">
                                    {selectedCompanyStats.accuracy.toFixed(1)}%
                                </div>
                                <div className="text-sm text-muted-foreground">Accuracy on this stock</div>
                            </div>
                        </div>
                    </CardHeader>
                    <CardContent className="space-y-6">
                        <div className="bg-muted/50 p-4 rounded-lg flex items-start gap-3 text-sm text-muted-foreground">
                            <Info className="h-5 w-5 text-blue-500 shrink-0 mt-0.5" />
                            <div>
                                <p className="font-medium text-foreground mb-1">How accuracy is calculated:</p>
                                <p>A rating is considered accurate if the direction matches the stock's performance over the following period:</p>
                                <ul className="list-disc list-inside mt-1 ml-1 space-y-1">
                                    <li><strong>Buy/Strong Buy:</strong> Positive return (&gt; 5%)</li>
                                    <li><strong>Sell/Strong Sell:</strong> Negative return (&lt; -5%)</li>
                                    <li><strong>Hold:</strong> Return within ±10%</li>
                                </ul>
                            </div>
                        </div>

                        <div>
                            <h3 className="text-lg font-semibold mb-3">Rating Timeline</h3>
                            <Table>
                                <TableHeader>
                                    <TableRow>
                                        <TableHead>Date</TableHead>
                                        <TableHead>Rating</TableHead>
                                        <TableHead>Price Target</TableHead>
                                        <TableHead>Result</TableHead>
                                        <TableHead className="text-right">Return</TableHead>
                                    </TableRow>
                                </TableHeader>
                                <TableBody>
                                    {selectedCompanyStats.ratings.map((rating, idx) => (
                                        <TableRow key={idx}>
                                            <TableCell className="font-medium">
                                                {new Date(rating.date).toLocaleDateString()}
                                            </TableCell>
                                            <TableCell>{getRatingBadge(rating.rating)}</TableCell>
                                            <TableCell>
                                                {rating.price_target ? `$${rating.price_target.toFixed(2)}` : "-"}
                                            </TableCell>
                                            <TableCell>{getAccuracyBadge(rating.was_accurate)}</TableCell>
                                            <TableCell className="text-right">
                                                {rating.actual_return !== null ? (
                                                    <span
                                                        className={
                                                            rating.actual_return >= 0 ? "text-emerald-600 font-bold" : "text-red-600 font-bold"
                                                        }
                                                    >
                                                        {(rating.actual_return * 100).toFixed(1)}%
                                                    </span>
                                                ) : (
                                                    "-"
                                                )}
                                            </TableCell>
                                        </TableRow>
                                    ))}
                                </TableBody>
                            </Table>
                        </div>
                    </CardContent>
                </Card>
            ) : groupByCompany ? (
                // Grouped Company List View
                <Card>
                    <CardHeader>
                        <CardTitle>Company Performance Overview</CardTitle>
                        <CardDescription>
                            Summary of analyst performance grouped by company ticker
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        <Table>
                            <TableHeader>
                                <TableRow>
                                    <TableHead>Company</TableHead>
                                    <TableHead className="text-center">Total Ratings</TableHead>
                                    <TableHead className="text-center">Accuracy</TableHead>
                                    <TableHead>Coverage Period</TableHead>
                                    <TableHead></TableHead>
                                </TableRow>
                            </TableHeader>
                            <TableBody>
                                {companyStats.map((stat) => (
                                    <TableRow
                                        key={stat.ticker}
                                        className="cursor-pointer hover:bg-muted/50 transition-colors"
                                        onClick={() => setSelectedCompany(stat.ticker)}
                                    >
                                        <TableCell>
                                            <div className="font-medium">{stat.ticker}</div>
                                            <div className="text-xs text-muted-foreground">{stat.name}</div>
                                        </TableCell>
                                        <TableCell className="text-center">
                                            <Badge variant="secondary" className="px-3">
                                                {stat.ratingsCount}
                                            </Badge>
                                        </TableCell>
                                        <TableCell className="text-center">
                                            <span className={`font-bold ${stat.accuracy >= 60 ? "text-emerald-600" :
                                                stat.accuracy >= 40 ? "text-amber-600" : "text-red-600"
                                                }`}>
                                                {stat.accuracy.toFixed(1)}%
                                            </span>
                                        </TableCell>
                                        <TableCell className="text-sm text-muted-foreground">
                                            {stat.firstRating.toLocaleDateString()} - {stat.lastRating.toLocaleDateString()}
                                        </TableCell>
                                        <TableCell className="text-right">
                                            <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                                                <ChevronRight className="h-4 w-4" />
                                            </Button>
                                        </TableCell>
                                    </TableRow>
                                ))}
                            </TableBody>
                        </Table>
                    </CardContent>
                </Card>
            ) : (
                // Original All Ratings View
                <Card>
                    <CardHeader>
                        <CardTitle>All Ratings History</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <Table>
                            <TableHeader>
                                <TableRow>
                                    <TableHead>Company</TableHead>
                                    <TableHead>Date</TableHead>
                                    <TableHead>Rating</TableHead>
                                    <TableHead>Price Target</TableHead>
                                    <TableHead>Result</TableHead>
                                    <TableHead>Return</TableHead>
                                </TableRow>
                            </TableHeader>
                            <TableBody>
                                {analyst.ratings.map((rating, idx) => (
                                    <TableRow key={idx}>
                                        <TableCell>
                                            <Link
                                                href={`/companies/${rating.ticker}`}
                                                className="text-blue-600 hover:underline font-medium"
                                            >
                                                {rating.ticker}
                                            </Link>
                                            {rating.company_name && (
                                                <span className="text-muted-foreground text-sm ml-2">
                                                    {rating.company_name}
                                                </span>
                                            )}
                                        </TableCell>
                                        <TableCell className="text-muted-foreground">
                                            {new Date(rating.date).toLocaleDateString()}
                                        </TableCell>
                                        <TableCell>{getRatingBadge(rating.rating)}</TableCell>
                                        <TableCell>
                                            {rating.price_target ? `$${rating.price_target.toFixed(2)}` : "-"}
                                        </TableCell>
                                        <TableCell>{getAccuracyBadge(rating.was_accurate)}</TableCell>
                                        <TableCell>
                                            {rating.actual_return !== null ? (
                                                <span
                                                    className={
                                                        rating.actual_return >= 0 ? "text-emerald-600" : "text-red-600"
                                                    }
                                                >
                                                    {(rating.actual_return * 100).toFixed(1)}%
                                                </span>
                                            ) : (
                                                "-"
                                            )}
                                        </TableCell>
                                    </TableRow>
                                ))}
                            </TableBody>
                        </Table>
                    </CardContent>
                </Card>
            )}
        </div>
    );
}
