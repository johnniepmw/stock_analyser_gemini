# Stock Analyser

A stock analysis application that ranks analysts by their historical accuracy and uses those rankings to identify high-potential S&P 500 investments.

## Architecture

```
stock_analyser/
├── backend/
│   ├── app/
│   │   ├── providers/     # Pluggable data source layer
│   │   ├── models.py      # Database entities
│   │   ├── ingestion.py   # Data ingestion service
│   │   ├── ranking.py     # Ranking algorithms
│   │   └── main.py        # FastAPI application
│   └── requirements.txt
└── frontend/              # Next.js UI (coming soon)
```

## Quick Start

### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run data ingestion (limited for testing)
python -m app.cli all --limit 10

# Start API server
uvicorn app.main:app --reload
```

### API Endpoints

- `GET /api/analysts` - List analysts with pagination
- `GET /api/analysts/{id}` - Analyst details
- `GET /api/companies` - List companies with pagination
- `GET /api/companies/{ticker}` - Company details

## Data Providers

The app uses a provider abstraction layer allowing easy swapping of data sources:

- **YFinanceProvider**: Real S&P 500 data and analyst recommendations
- **MockProvider**: Synthetic data for testing
- **CompositeProvider**: Combine multiple sources
