const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface AnalystSummary {
    analyst_id: string;
    name: string;
    firm: string;
    confidence_score: number | null;
    total_ratings: number;
}

export interface RatingSummary {
    ticker: string;
    company_name: string | null;
    date: string;
    rating: string;
    price_target: number | null;
    was_accurate: boolean | null;
    actual_return: number | null;
}

export interface AnalystDetail extends AnalystSummary {
    accurate_ratings: number;
    ratings: RatingSummary[];
}

export interface CompanySummary {
    ticker: string;
    name: string;
    sector: string | null;
    current_price: number | null;
    target_price: number | null;
    investment_score: number | null;
}

export interface CompanyRating {
    analyst_id: string;
    analyst_name: string;
    firm: string;
    confidence_score: number | null;
    date: string;
    rating: string;
    price_target: number | null;
}

export interface CompanyDetail extends CompanySummary {
    industry: string | null;
    market_cap: number | null;
    analyst_ratings: CompanyRating[];
}

export interface PaginatedResponse<T> {
    items: T[];
    total: number;
    page: number;
    page_size: number;
    total_pages: number;
}

export async function fetchAnalysts(
    page = 1,
    pageSize = 20,
    sortBy = "confidence_score",
    sortOrder = "desc"
): Promise<PaginatedResponse<AnalystSummary>> {
    const url = `${API_BASE}/api/analysts?page=${page}&page_size=${pageSize}&sort_by=${sortBy}&sort_order=${sortOrder}`;
    const res = await fetch(url);
    if (!res.ok) throw new Error("Failed to fetch analysts");
    return res.json();
}

export async function fetchAnalyst(analystId: string): Promise<AnalystDetail> {
    const res = await fetch(`${API_BASE}/api/analysts/${analystId}`);
    if (!res.ok) throw new Error("Failed to fetch analyst");
    return res.json();
}

export async function fetchCompanies(
    page = 1,
    pageSize = 20,
    sortBy = "investment_score",
    sortOrder = "desc",
    sector?: string
): Promise<PaginatedResponse<CompanySummary>> {
    let url = `${API_BASE}/api/companies?page=${page}&page_size=${pageSize}&sort_by=${sortBy}&sort_order=${sortOrder}`;
    if (sector) url += `&sector=${encodeURIComponent(sector)}`;
    const res = await fetch(url);
    if (!res.ok) throw new Error("Failed to fetch companies");
    return res.json();
}

export async function fetchCompany(ticker: string): Promise<CompanyDetail> {
    const res = await fetch(`${API_BASE}/api/companies/${ticker}`);
    if (!res.ok) throw new Error("Failed to fetch company");
    return res.json();
}

export async function fetchSectors(): Promise<string[]> {
    const res = await fetch(`${API_BASE}/api/sectors`);
    if (!res.ok) throw new Error("Failed to fetch sectors");
    return res.json();
}

export interface StockPrice {
    date: string;
    open: number;
    high: number;
    low: number;
    close: number;
    volume: number;
}

export interface BenchmarkPrice {
    date: string;
    close: number;
}

export async function fetchCompanyPrices(
    ticker: string,
    startDate?: string,
    endDate?: string
): Promise<StockPrice[]> {
    let url = `${API_BASE}/api/companies/${ticker}/prices`;
    const params = new URLSearchParams();
    if (startDate) params.append("start_date", startDate);
    if (endDate) params.append("end_date", endDate);
    if (params.toString()) url += `?${params.toString()}`;

    const res = await fetch(url);
    if (!res.ok) throw new Error("Failed to fetch company prices");
    return res.json();
}

export async function fetchBenchmarkPrices(
    symbol: string,
    startDate?: string,
    endDate?: string
): Promise<BenchmarkPrice[]> {
    let url = `${API_BASE}/api/benchmark/${symbol}/prices`;
    const params = new URLSearchParams();
    if (startDate) params.append("start_date", startDate);
    if (endDate) params.append("end_date", endDate);
    if (params.toString()) url += `?${params.toString()}`;

    const res = await fetch(url);
    if (!res.ok) throw new Error("Failed to fetch benchmark prices");
    return res.json();
}
