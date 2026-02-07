"use client";

import { useState, useEffect } from "react";
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
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { fetchAnalysts, AnalystSummary, PaginatedResponse } from "@/lib/api";

function getConfidenceBadge(score: number | null) {
    if (score === null) return <Badge variant="outline">N/A</Badge>;
    if (score >= 70) return <Badge className="bg-emerald-500">{score.toFixed(1)}%</Badge>;
    if (score >= 50) return <Badge className="bg-amber-500">{score.toFixed(1)}%</Badge>;
    return <Badge className="bg-red-500">{score.toFixed(1)}%</Badge>;
}

export default function AnalystsPage() {
    const [data, setData] = useState<PaginatedResponse<AnalystSummary> | null>(null);
    const [page, setPage] = useState(1);
    const [sortBy, setSortBy] = useState("confidence_score");
    const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        setLoading(true);
        fetchAnalysts(page, 20, sortBy, sortOrder)
            .then(setData)
            .finally(() => setLoading(false));
    }, [page, sortBy, sortOrder]);

    const handleSort = (column: string) => {
        if (sortBy === column) {
            setSortOrder(sortOrder === "asc" ? "desc" : "asc");
        } else {
            setSortBy(column);
            setSortOrder("desc");
        }
    };

    return (
        <div className="container mx-auto py-8 px-4">
            <Card>
                <CardHeader>
                    <CardTitle className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                        Analysts
                    </CardTitle>
                    <p className="text-muted-foreground">
                        Ranked by confidence score based on historical prediction accuracy
                    </p>
                </CardHeader>
                <CardContent>
                    {loading ? (
                        <div className="flex justify-center py-12">
                            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                        </div>
                    ) : (
                        <>
                            <Table>
                                <TableHeader>
                                    <TableRow>
                                        <TableHead
                                            className="cursor-pointer hover:text-blue-600"
                                            onClick={() => handleSort("name")}
                                        >
                                            Name {sortBy === "name" && (sortOrder === "asc" ? "↑" : "↓")}
                                        </TableHead>
                                        <TableHead
                                            className="cursor-pointer hover:text-blue-600"
                                            onClick={() => handleSort("firm")}
                                        >
                                            Firm {sortBy === "firm" && (sortOrder === "asc" ? "↑" : "↓")}
                                        </TableHead>
                                        <TableHead
                                            className="cursor-pointer hover:text-blue-600"
                                            onClick={() => handleSort("confidence_score")}
                                        >
                                            Confidence {sortBy === "confidence_score" && (sortOrder === "asc" ? "↑" : "↓")}
                                        </TableHead>
                                        <TableHead
                                            className="cursor-pointer hover:text-blue-600"
                                            onClick={() => handleSort("total_ratings")}
                                        >
                                            Ratings {sortBy === "total_ratings" && (sortOrder === "asc" ? "↑" : "↓")}
                                        </TableHead>
                                    </TableRow>
                                </TableHeader>
                                <TableBody>
                                    {data?.items.map((analyst) => (
                                        <TableRow key={analyst.analyst_id} className="hover:bg-muted/50">
                                            <TableCell>
                                                <Link
                                                    href={`/analysts/${analyst.analyst_id}`}
                                                    className="text-blue-600 hover:underline font-medium"
                                                >
                                                    {analyst.name}
                                                </Link>
                                            </TableCell>
                                            <TableCell className="text-muted-foreground">{analyst.firm}</TableCell>
                                            <TableCell>{getConfidenceBadge(analyst.confidence_score)}</TableCell>
                                            <TableCell>{analyst.total_ratings}</TableCell>
                                        </TableRow>
                                    ))}
                                </TableBody>
                            </Table>

                            {/* Pagination */}
                            <div className="flex items-center justify-between mt-4">
                                <p className="text-sm text-muted-foreground">
                                    Page {data?.page} of {data?.total_pages} ({data?.total} total)
                                </p>
                                <div className="flex gap-2">
                                    <Button
                                        variant="outline"
                                        size="sm"
                                        disabled={page <= 1}
                                        onClick={() => setPage(page - 1)}
                                    >
                                        Previous
                                    </Button>
                                    <Button
                                        variant="outline"
                                        size="sm"
                                        disabled={page >= (data?.total_pages || 1)}
                                        onClick={() => setPage(page + 1)}
                                    >
                                        Next
                                    </Button>
                                </div>
                            </div>
                        </>
                    )}
                </CardContent>
            </Card>
        </div>
    );
}
