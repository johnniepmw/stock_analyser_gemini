"use client";

import { useEffect, useState } from "react";
import {
    fetchDataSources,
    activateDataSource,
    fetchJobs,
    triggerJob,
    DataSource,
    Job
} from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Loader2, RefreshCw, database, Play } from "lucide-react";

export default function AdminPage() {
    const [dataSources, setDataSources] = useState<Record<string, DataSource[]>>({});
    const [jobs, setJobs] = useState<Job[]>([]);
    const [loading, setLoading] = useState(true);
    const [triggering, setTriggering] = useState<string | null>(null);

    const loadData = async () => {
        try {
            const [sourcesData, jobsData] = await Promise.all([
                fetchDataSources(),
                fetchJobs()
            ]);
            setDataSources(sourcesData);
            setJobs(jobsData);
        } catch (error) {
            console.error("Failed to load admin data:", error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadData();
        // Poll for job updates every 5 seconds
        const interval = setInterval(loadData, 5000);
        return () => clearInterval(interval);
    }, []);

    const handleActivate = async (source: DataSource) => {
        if (source.is_active) return;
        try {
            await activateDataSource(source.id);
            await loadData();
        } catch (error) {
            console.error("Failed to activate source:", error);
        }
    };

    const handleTriggerJob = async (jobType: string) => {
        setTriggering(jobType);
        try {
            await triggerJob(jobType);
            await loadData();
        } catch (error) {
            console.error("Failed to trigger job:", error);
        } finally {
            setTriggering(null);
        }
    };

    const getJobStatusBadge = (status: string) => {
        const styles: Record<string, string> = {
            pending: "bg-gray-500",
            running: "bg-blue-500 animate-pulse",
            completed: "bg-emerald-500",
            failed: "bg-red-500",
        };
        return <Badge className={styles[status] || "bg-gray-500"}>{status.toUpperCase()}</Badge>;
    };

    if (loading) {
        return (
            <div className="flex justify-center items-center min-h-screen">
                <Loader2 className="h-8 w-8 animate-spin text-emerald-600" />
            </div>
        );
    }

    return (
        <div className="container mx-auto py-8 px-4 space-y-6">
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-3xl font-bold">Admin Dashboard</h1>
                    <p className="text-muted-foreground">Manage data sources and ingestion jobs</p>
                </div>
                <Button variant="outline" onClick={loadData}>
                    <RefreshCw className="mr-2 h-4 w-4" />
                    Refresh
                </Button>
            </div>

            <Tabs defaultValue="datasources" className="w-full">
                <TabsList>
                    <TabsTrigger value="datasources">Data Sources</TabsTrigger>
                    <TabsTrigger value="jobs">Job History</TabsTrigger>
                </TabsList>

                <TabsContent value="datasources" className="space-y-6 mt-4">
                    {Object.entries(dataSources).map(([category, sources]) => (
                        <Card key={category}>
                            <CardHeader>
                                <CardTitle className="capitalize">{category.replace(/_/g, " ")}</CardTitle>
                                <CardDescription>Configure active provider for this category</CardDescription>
                            </CardHeader>
                            <CardContent>
                                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                                    {sources.map(source => (
                                        <div
                                            key={source.id}
                                            className={`
                                                flex flex-col justify-between p-4 rounded-lg border 
                                                ${source.is_active ? "border-emerald-500 bg-emerald-50/10" : "border-border"}
                                            `}
                                        >
                                            <div className="space-y-2">
                                                <div className="flex justify-between items-start">
                                                    <h3 className="font-semibold">{source.name}</h3>
                                                    {source.is_active && <Badge className="bg-emerald-600">Active</Badge>}
                                                </div>
                                                <div className="text-xs text-muted-foreground">
                                                    Last updated: {source.last_updated ? new Date(source.last_updated).toLocaleString() : "Never"}
                                                </div>
                                            </div>
                                            <div className="mt-4 flex items-center space-x-2">
                                                <Switch
                                                    id={`source-${source.id}`}
                                                    checked={source.is_active}
                                                    onCheckedChange={() => handleActivate(source)}
                                                    disabled={source.is_active}
                                                />
                                                <Label htmlFor={`source-${source.id}`}>
                                                    {source.is_active ? "Enabled" : "Enable"}
                                                </Label>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </CardContent>
                        </Card>
                    ))}
                </TabsContent>

                <TabsContent value="jobs" className="space-y-6 mt-4">
                    <Card>
                        <CardHeader>
                            <CardTitle>Ingestion Jobs</CardTitle>
                            <CardDescription>
                                Trigger and monitor background data ingestion tasks
                            </CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-6">
                            <div className="flex flex-wrap gap-4">
                                <Button
                                    onClick={() => handleTriggerJob("ingest_prices")}
                                    disabled={!!triggering}
                                >
                                    {triggering === "ingest_prices" ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Play className="mr-2 h-4 w-4" />}
                                    Ingest Prices (5y)
                                </Button>
                                <Button
                                    onClick={() => handleTriggerJob("ingest_companies")}
                                    disabled={!!triggering}
                                    variant="secondary"
                                >
                                    {triggering === "ingest_companies" ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Play className="mr-2 h-4 w-4" />}
                                    Update S&P 500 List
                                </Button>
                                <Button
                                    onClick={() => handleTriggerJob("ingest_ratings")}
                                    disabled={!!triggering}
                                    variant="secondary"
                                >
                                    {triggering === "ingest_ratings" ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Play className="mr-2 h-4 w-4" />}
                                    Ingest Ratings
                                </Button>
                                <Button
                                    onClick={() => handleTriggerJob("ingest_benchmark")}
                                    disabled={!!triggering}
                                    variant="secondary"
                                >
                                    {triggering === "ingest_benchmark" ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Play className="mr-2 h-4 w-4" />}
                                    Ingest Benchmark (SPY)
                                </Button>
                            </div>

                            <div className="rounded-md border">
                                <Table>
                                    <TableHeader>
                                        <TableRow>
                                            <TableHead>Type</TableHead>
                                            <TableHead>Status</TableHead>
                                            <TableHead>Start Time</TableHead>
                                            <TableHead>Duration</TableHead>
                                            <TableHead>Details</TableHead>
                                        </TableRow>
                                    </TableHeader>
                                    <TableBody>
                                        {jobs.length > 0 ? (
                                            jobs.map((job) => (
                                                <TableRow key={job.id}>
                                                    <TableCell className="font-medium">{job.job_type}</TableCell>
                                                    <TableCell>{getJobStatusBadge(job.status)}</TableCell>
                                                    <TableCell>{new Date(job.start_time).toLocaleString()}</TableCell>
                                                    <TableCell>
                                                        {job.end_time
                                                            ? ((new Date(job.end_time).getTime() - new Date(job.start_time).getTime()) / 1000).toFixed(1) + "s"
                                                            : "-"
                                                        }
                                                    </TableCell>
                                                    <TableCell className="text-muted-foreground text-sm max-w-xs truncate" title={job.details || ""}>
                                                        {job.details || "-"}
                                                    </TableCell>
                                                </TableRow>
                                            ))
                                        ) : (
                                            <TableRow>
                                                <TableCell colSpan={5} className="text-center h-24 text-muted-foreground">
                                                    No jobs run recently
                                                </TableCell>
                                            </TableRow>
                                        )}
                                    </TableBody>
                                </Table>
                            </div>
                        </CardContent>
                    </Card>
                </TabsContent>
            </Tabs>
        </div>
    );
}
