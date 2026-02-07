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
import {
    fetchCompanies,
    fetchSectors,
    CompanySummary,
    PaginatedResponse,
} from "@/lib/api";

function getScoreBadge(score: number | null) {
    if (score === null) return <Badge variant="outline">N/A</Badge>;
    if (score >= 75) return <Badge className="bg-emerald-500">{score.toFixed(0)}</Badge>;
    if (score >= 50) return <Badge className="bg-amber-500">{score.toFixed(0)}</Badge>;
    return <Badge className="bg-red-500">{score.toFixed(0)}</Badge>;
}

function getUpsideBadge(current: number | null, target: number | null) {
    if (!current || !target) return <span className="text-muted-foreground">-</span>;
    const upside = ((target - current) / current) * 100;
    const color = upside >= 0 ? "text-emerald-600" : "text-red-600";
    return <span className={`font-medium ${color}`}>{upside >= 0 ? "+" : ""}{upside.toFixed(1)}%</span>;
}

export default function CompaniesPage() {
    const [data, setData] = useState<PaginatedResponse<CompanySummary> | null>(null);
    const [sectors, setSectors] = useState<string[]>([]);
    const [page, setPage] = useState(1);
    const [sortBy, setSortBy] = useState("investment_score");
    const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");
    const [selectedSector, setSelectedSector] = useState<string | undefined>();
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchSectors().then(setSectors);
    }, []);

    useEffect(() => {
        setLoading(true);
        fetchCompanies(page, 20, sortBy, sortOrder, selectedSector)
            .then(setData)
            .finally(() => setLoading(false));
    }, [page, sortBy, sortOrder, selectedSector]);

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
                    <CardTitle className="text-2xl font-bold bg-gradient-to-r from-emerald-600 to-teal-600 bg-clip-text text-transparent">
                        Companies
                    </CardTitle>
                    <p className="text-muted-foreground">
                        S&P 500 companies ranked by investment potential
                    </p>

                    {/* Sector Filter */}
                    <div className="flex flex-wrap gap-2 mt-4">
                        <Button
                            variant={!selectedSector ? "default" : "outline"}
                            size="sm"
                            onClick={() => setSelectedSector(undefined)}
                        >
                            All Sectors
                        </Button>
                        {sectors.slice(0, 8).map((sector) => (
                            <Button
                                key={sector}
                                variant={selectedSector === sector ? "default" : "outline"}
                                size="sm"
                                onClick={() => setSelectedSector(sector)}
                            >
                                {sector}
                            </Button>
                        ))}
                    </div>
                </CardHeader>
                <CardContent>
                    {loading ? (
                        <div className="flex justify-center py-12">
                            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-600"></div>
                        </div>
                    ) : (
                        <>
                            <Table>
                                <TableHeader>
                                    <TableRow>
                                        <TableHead>Ticker</TableHead>
                                        <TableHead
                                            className="cursor-pointer hover:text-emerald-600"
                                            onClick={() => handleSort("name")}
                                        >
                                            Name {sortBy === "name" && (sortOrder === "asc" ? "↑" : "↓")}
                                        </TableHead>
                                        <TableHead
                                            className="cursor-pointer hover:text-emerald-600"
                                            onClick={() => handleSort("sector")}
                                        >
                                            Sector {sortBy === "sector" && (sortOrder === "asc" ? "↑" : "↓")}
                                        </TableHead>
                                        <TableHead
                                            className="cursor-pointer hover:text-emerald-600"
                                            onClick={() => handleSort("current_price")}
                                        >
                                            Price {sortBy === "current_price" && (sortOrder === "asc" ? "↑" : "↓")}
                                        </TableHead>
                                        <TableHead>Target</TableHead>
                                        <TableHead>Upside</TableHead>
                                        <TableHead
                                            className="cursor-pointer hover:text-emerald-600"
                                            onClick={() => handleSort("investment_score")}
                                        >
                                            Score {sortBy === "investment_score" && (sortOrder === "asc" ? "↑" : "↓")}
                                        </TableHead>
                                    </TableRow>
                                </TableHeader>
                                <TableBody>
                                    {data?.items.map((company) => (
                                        <TableRow key={company.ticker} className="hover:bg-muted/50">
                                            <TableCell>
                                                <Link
                                                    href={`/companies/${company.ticker}`}
                                                    className="text-emerald-600 hover:underline font-bold"
                                                >
                                                    {company.ticker}
                                                </Link>
                                            </TableCell>
                                            <TableCell className="font-medium">{company.name}</TableCell>
                                            <TableCell>
                                                <Badge variant="secondary">{company.sector || "N/A"}</Badge>
                                            </TableCell>
                                            <TableCell>
                                                {company.current_price
                                                    ? `$${company.current_price.toFixed(2)}`
                                                    : "-"}
                                            </TableCell>
                                            <TableCell>
                                                {company.target_price
                                                    ? `$${company.target_price.toFixed(2)}`
                                                    : "-"}
                                            </TableCell>
                                            <TableCell>
                                                {getUpsideBadge(company.current_price, company.target_price)}
                                            </TableCell>
                                            <TableCell>{getScoreBadge(company.investment_score)}</TableCell>
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
