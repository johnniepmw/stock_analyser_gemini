"use client";

import { useState, useEffect } from "react";
import {
    LineChart,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    Legend,
    ResponsiveContainer,
} from "recharts";
import { Card, CardContent } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { fetchCompanyPrices, fetchBenchmarkPrices, StockPrice, BenchmarkPrice } from "@/lib/api";

interface HistoricPerformanceChartProps {
    ticker: string;
    companyName: string;
}

export function HistoricPerformanceChart({ ticker, companyName }: HistoricPerformanceChartProps) {
    const [prices, setPrices] = useState<StockPrice[]>([]);
    const [benchmarkPrices, setBenchmarkPrices] = useState<BenchmarkPrice[]>([]);
    const [showBenchmark, setShowBenchmark] = useState(false);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        async function loadData() {
            setLoading(true);
            setError(null);
            try {
                // Fetch company data
                const companyData = await fetchCompanyPrices(ticker);
                setPrices(companyData);

                // Fetch benchmark data independently so it's ready when toggled
                // We'll use SPY as the default benchmark
                const benchmarkData = await fetchBenchmarkPrices("SPY");
                setBenchmarkPrices(benchmarkData);
            } catch (err) {
                setError("Failed to load price data");
                console.error(err);
            } finally {
                setLoading(false);
            }
        }
        loadData();
    }, [ticker]);

    if (loading) {
        return <div className="h-[400px] flex items-center justify-center">Loading chart data...</div>;
    }

    if (error) {
        return <div className="h-[400px] flex items-center justify-center text-red-500">{error}</div>;
    }

    if (prices.length === 0) {
        return <div className="h-[400px] flex items-center justify-center text-muted-foreground">No price data available</div>;
    }

    // Merge and normalize data for valid comparison
    // We align by date and calculate percentage change from the first available date common to both

    // Create a map of benchmark prices for O(1) lookup
    const benchmarkMap = new Map(benchmarkPrices.map(p => [p.date.split("T")[0], p.close]));

    const data = prices.map(p => {
        const dateStr = p.date.split("T")[0];
        const benchmarkPrice = benchmarkMap.get(dateStr);
        return {
            date: dateStr,
            fullDate: p.date,
            companyPrice: p.close,
            benchmarkPrice: benchmarkPrice,
        };
    }).filter(d => d.companyPrice !== undefined && (!showBenchmark || d.benchmarkPrice !== undefined));

    if (data.length === 0) return <div>No overlapping data found</div>;

    const baseCompany = data[0].companyPrice;
    const baseBenchmark = data[0].benchmarkPrice || 1; // avoid divide by zero if missing

    const normalizedData = data.map(d => ({
        ...d,
        companyPct: ((d.companyPrice - baseCompany) / baseCompany) * 100,
        benchmarkPct: d.benchmarkPrice ? ((d.benchmarkPrice - baseBenchmark) / baseBenchmark) * 100 : null,
    }));

    return (
        <div className="space-y-4">
            <div className="flex items-center space-x-2">
                <Checkbox
                    id="show-benchmark"
                    checked={showBenchmark}
                    onCheckedChange={(checked: boolean | "indeterminate") => setShowBenchmark(checked === true)}
                />
                <Label htmlFor="show-benchmark" className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">
                    Compare with S&P 500 (SPY)
                </Label>
            </div>

            <Card>
                <CardContent className="p-6">
                    <div className="h-[400px] w-full">
                        <ResponsiveContainer width="100%" height="100%">
                            <LineChart data={normalizedData}>
                                <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
                                <XAxis
                                    dataKey="date"
                                    tickFormatter={(val) => new Date(val).toLocaleDateString(undefined, { month: 'short', year: '2-digit' })}
                                    minTickGap={30}
                                />
                                <YAxis
                                    unit="%"
                                    domain={['auto', 'auto']}
                                />
                                <Tooltip
                                    labelFormatter={(val) => new Date(val).toLocaleDateString()}
                                    formatter={(value: number | string | Array<number | string> | undefined, name: string | undefined) => [
                                        value !== undefined ? `${Number(value).toFixed(2)}%` : "N/A",
                                        name === "companyPct" ? companyName : "S&P 500"
                                    ]}
                                />
                                <Legend />
                                <Line
                                    type="monotone"
                                    dataKey="companyPct"
                                    name={companyName}
                                    stroke="#10b981"
                                    strokeWidth={2}
                                    dot={false}
                                />
                                {showBenchmark && (
                                    <Line
                                        type="monotone"
                                        dataKey="benchmarkPct"
                                        name="S&P 500"
                                        stroke="#64748b"
                                        strokeWidth={2}
                                        strokeDasharray="5 5"
                                        dot={false}
                                    />
                                )}
                            </LineChart>
                        </ResponsiveContainer>
                    </div>
                </CardContent>
            </Card>
        </div>
    );
}
