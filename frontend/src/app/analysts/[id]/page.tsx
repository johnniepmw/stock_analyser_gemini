"use client";

import { useState, useEffect } from "react";
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
import { fetchAnalyst, AnalystDetail } from "@/lib/api";

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

export default function AnalystDetailPage() {
    const params = useParams();
    const analystId = params.id as string;
    const [analyst, setAnalyst] = useState<AnalystDetail | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        setLoading(true);
        fetchAnalyst(analystId)
            .then(setAnalyst)
            .finally(() => setLoading(false));
    }, [analystId]);

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

    return (
        <div className="container mx-auto py-8 px-4 space-y-6">
            {/* Header Card */}
            <Card>
                <CardHeader>
                    <div className="flex items-center gap-4">
                        <Link href="/analysts" className="text-blue-600 hover:underline text-sm">
                            ← Back to Analysts
                        </Link>
                    </div>
                    <CardTitle className="text-3xl font-bold">{analyst.name}</CardTitle>
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
                            <p className="text-sm text-muted-foreground">Accuracy Rate</p>
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

            {/* Ratings Table */}
            <Card>
                <CardHeader>
                    <CardTitle>Rating History</CardTitle>
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
        </div>
    );
}
