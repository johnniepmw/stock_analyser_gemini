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
import { fetchCompany, CompanyDetail } from "@/lib/api";

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

function getConfidenceBadge(score: number | null) {
    if (score === null) return <Badge variant="outline">N/A</Badge>;
    if (score >= 70) return <Badge className="bg-blue-500">{score.toFixed(0)}%</Badge>;
    if (score >= 50) return <Badge className="bg-amber-500">{score.toFixed(0)}%</Badge>;
    return <Badge className="bg-gray-400">{score.toFixed(0)}%</Badge>;
}

export default function CompanyDetailPage() {
    const params = useParams();
    const ticker = params.ticker as string;
    const [company, setCompany] = useState<CompanyDetail | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        setLoading(true);
        fetchCompany(ticker)
            .then(setCompany)
            .finally(() => setLoading(false));
    }, [ticker]);

    if (loading) {
        return (
            <div className="flex justify-center items-center min-h-screen">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-600"></div>
            </div>
        );
    }

    if (!company) {
        return (
            <div className="container mx-auto py-8 px-4">
                <Card>
                    <CardContent className="py-12 text-center">
                        <p className="text-muted-foreground">Company not found</p>
                    </CardContent>
                </Card>
            </div>
        );
    }

    const upside =
        company.current_price && company.target_price
            ? ((company.target_price - company.current_price) / company.current_price) * 100
            : null;

    return (
        <div className="container mx-auto py-8 px-4 space-y-6">
            {/* Header Card */}
            <Card>
                <CardHeader>
                    <div className="flex items-center gap-4">
                        <Link href="/companies" className="text-emerald-600 hover:underline text-sm">
                            ← Back to Companies
                        </Link>
                    </div>
                    <div className="flex items-center gap-4">
                        <CardTitle className="text-4xl font-bold">{company.ticker}</CardTitle>
                        <Badge variant="secondary" className="text-lg">{company.sector}</Badge>
                    </div>
                    <CardDescription className="text-xl">{company.name}</CardDescription>
                </CardHeader>
                <CardContent>
                    <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                        <div className="bg-gradient-to-br from-emerald-500/10 to-teal-500/10 rounded-lg p-4">
                            <p className="text-sm text-muted-foreground">Current Price</p>
                            <p className="text-2xl font-bold text-emerald-600">
                                ${company.current_price?.toFixed(2) || "N/A"}
                            </p>
                        </div>
                        <div className="bg-gradient-to-br from-blue-500/10 to-indigo-500/10 rounded-lg p-4">
                            <p className="text-sm text-muted-foreground">Target Price</p>
                            <p className="text-2xl font-bold text-blue-600">
                                ${company.target_price?.toFixed(2) || "N/A"}
                            </p>
                        </div>
                        <div className="bg-gradient-to-br from-purple-500/10 to-pink-500/10 rounded-lg p-4">
                            <p className="text-sm text-muted-foreground">Upside Potential</p>
                            <p
                                className={`text-2xl font-bold ${upside !== null && upside >= 0 ? "text-emerald-600" : "text-red-600"
                                    }`}
                            >
                                {upside !== null ? `${upside >= 0 ? "+" : ""}${upside.toFixed(1)}%` : "N/A"}
                            </p>
                        </div>
                        <div className="bg-gradient-to-br from-amber-500/10 to-orange-500/10 rounded-lg p-4">
                            <p className="text-sm text-muted-foreground">Investment Score</p>
                            <p className="text-2xl font-bold text-amber-600">
                                {company.investment_score?.toFixed(0) || "N/A"}
                            </p>
                        </div>
                        <div className="bg-gradient-to-br from-gray-500/10 to-slate-500/10 rounded-lg p-4">
                            <p className="text-sm text-muted-foreground">Industry</p>
                            <p className="text-lg font-medium text-gray-700 dark:text-gray-300">
                                {company.industry || "N/A"}
                            </p>
                        </div>
                    </div>
                </CardContent>
            </Card>

            {/* Analyst Ratings Table */}
            <Card>
                <CardHeader>
                    <CardTitle>Analyst Ratings</CardTitle>
                    <CardDescription>
                        Current analyst recommendations weighted by their confidence scores
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    <Table>
                        <TableHeader>
                            <TableRow>
                                <TableHead>Analyst</TableHead>
                                <TableHead>Firm</TableHead>
                                <TableHead>Confidence</TableHead>
                                <TableHead>Date</TableHead>
                                <TableHead>Rating</TableHead>
                                <TableHead>Price Target</TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {company.analyst_ratings.map((rating, idx) => (
                                <TableRow key={idx}>
                                    <TableCell>
                                        <Link
                                            href={`/analysts/${rating.analyst_id}`}
                                            className="text-blue-600 hover:underline font-medium"
                                        >
                                            {rating.analyst_name}
                                        </Link>
                                    </TableCell>
                                    <TableCell className="text-muted-foreground">{rating.firm}</TableCell>
                                    <TableCell>{getConfidenceBadge(rating.confidence_score)}</TableCell>
                                    <TableCell className="text-muted-foreground">
                                        {new Date(rating.date).toLocaleDateString()}
                                    </TableCell>
                                    <TableCell>{getRatingBadge(rating.rating)}</TableCell>
                                    <TableCell>
                                        {rating.price_target ? `$${rating.price_target.toFixed(2)}` : "-"}
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
