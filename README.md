## PhoneWise – Smart Phone Recommendation App

PhoneWise is a full-stack web application that recommends smartphones based on your budget, usage patterns, and hardware priorities. It uses a curated specs database (scraped from `phonedb.net`) stored in MongoDB, and a scoring engine that ranks phones with explainable reasons.

---

### 1. High-Level Architecture

```mermaid
flowchart LR
  U[User] --> FE[React + Tailwind SPA]
  FE -->|REST JSON| BE[FastAPI backend]
  BE -->|read/write| DB[(MongoDB)]
  BE -->|import & trigger| SCR[Scraper (requests + BeautifulSoup)]
  SCR -->|upsert phones| DB
```

- **Frontend**: React + Vite + Tailwind CSS, with pages for landing, preferences, results, comparison, and admin.
- **Backend**: FastAPI + Pydantic + PyMongo exposing:
  - `GET /phones`
  - `POST /recommend`
  - `POST /update-database`
  - `GET /health`
- **Database**: MongoDB (Atlas or local) storing normalized phone specs.
- **Scraper**: Standalone Python module using `requests` + `BeautifulSoup` to fetch device specs from `https://phonedb.net/` and upsert into MongoDB.

---

### 2. Folder Structure

```text
backend/
  app/
    config.py           # Settings, env variables
    db.py               # MongoDB client and helpers
    models.py           # Pydantic models for phones and recommendations
    recommendation.py   # Scoring and explanation engine
    main.py             # FastAPI app & routes
  requirements.txt      # Backend + scraper Python dependencies
  .env.example          # Sample env file for backend

scraper/
  __init__.py
  scrape_phones.py      # Scraper for phonedb.net that populates MongoDB

frontend/
  package.json
  vite.config.ts
  tailwind.config.js
  postcss.config.js
  tsconfig.json
  index.html
  src/
    main.tsx
    App.tsx
    index.css
    types.ts
    lib/api.ts
    hooks/useTheme.ts
    components/
      Layout.tsx
      ThemeToggle.tsx
      PreferenceForm.tsx
      PhoneCard.tsx
      RecommendationReason.tsx
      TagPill.tsx
      LoadingSpinner.tsx
      ErrorBanner.tsx
      ComparisonTable.tsx
    routes/
      Landing.tsx
      Preferences.tsx
      Results.tsx
      Compare.tsx
      Admin.tsx
```

---

### 3. Backend Overview

- **Tech**: Python 3.10+, FastAPI, PyMongo, Pydantic v2, python-dotenv.
- **Config**: `backend/app/config.py` reads environment variables:

  - `MONGO_URI` – MongoDB connection string (Atlas or local).
  - `MONGO_DB` – database name, default `phone_recommender`.
  - `PHONES_COLLECTION` – collection name, default `phones`.
  - `API_SECRET_TOKEN` – shared secret token for `/update-database`.

- **DB helper** `backend/app/db.py`:
  - Creates a `MongoClient` and `phones` collection with indexes.
  - Provides `upsert_phone(phone_dict)` using `name` as the unique key.

- **Models** (`backend/app/models.py`):
  - `PhoneInDB` – normalized phone document (name, price, battery, ram, storage, camera, chipset, os, id).
  - `RecommendationRequest` – user preferences (budget, min RAM, storage, OS preference, primary use, weights).
  - `PhoneRecommendation` / `RecommendationResponse` – recommendation payload with match score, percentage, reasons, and tags.

- **Recommendation engine** (`backend/app/recommendation.py`):
  - Normalizes continuous features (price, battery, RAM, storage, camera).
  - Computes a weighted score:

    \[
    score = (w_b \cdot S_{budget}) + (w_c \cdot S_{camera}) + (w_{bat} \cdot S_{battery}) + (w_p \cdot S_{performance}) + (w_s \cdot S_{storage}) + (w_r \cdot S_{ram})
    \]

  - Performance score is inferred from chipset and RAM (gaming / midrange heuristics).
  - Builds tags such as &ldquo;Great for gaming&rdquo;, &ldquo;Exceptional battery life&rdquo;, etc.
  - Generates human-readable reasons explaining **why** each phone was chosen.

- **API routes** (`backend/app/main.py`):
  - `GET /phones`: List phones, optional filters by `os` and `max_price`.
  - `POST /recommend`: Accepts `RecommendationRequest`, scores phones using the engine and returns top matches.
  - `POST /update-database`: Protected by `API_SECRET_TOKEN`; triggers the scraper and clears in-memory cache.
  - `GET /health`: Simple health check.
  - In-memory caching of recommendation results (5-minute TTL) to avoid re-scoring identical requests.

---

### 4. Scraper Module (phonedb.net)

**Location**: `scraper/scrape_phones.py`

**What it does**

- Hits `https://phonedb.net/index.php?m=device&s=list` to discover device links.
- For each device, navigates to the detailed specs page (`&d=detailed_specs`).
- Parses the spec tables to extract:
  - `name` (Model)
  - `battery` (mAh, from &ldquo;Nominal Battery Capacity&rdquo;)
  - `ram` (GB, from &ldquo;RAM Capacity&rdquo; in MiB/GiB)
  - `storage` (GB, from &ldquo;Non-volatile Memory Capacity&rdquo; in MiB/GiB)
  - `camera` (MP, from &ldquo;Number of effective pixels&rdquo;)
  - `chipset` (CPU description)
  - `os` (from Platform/Operating System)
  - `country="India"`, `currency="INR"`, `source="phonedb.net"`
- Sets `price = 0.0` for all records because PhoneDB does not expose INR pricing.
  - You can later enrich price manually or via another data source.
- Performs **upserts** via `backend.app.db.upsert_phone`, keyed on `name`.

**Safety & quality**

- Custom `User-Agent`, request timeout, and **1.5s delay** between device requests to avoid hammering the site.
- Logging and exception handling per device; failures for individual devices do not stop the whole run.

**Entry point**

- `run_scraper(max_devices: int = 150)`:
  - Returns the number of successfully upserted phone records.
  - Used by both the backend `/update-database` route and CLI (`python -m scraper.scrape_phones`).

---

### 5. Frontend Overview (React + Tailwind)

**Tech stack**

- React 18 + Vite + TypeScript.
- Tailwind CSS with `darkMode: "class"` and a custom theme.
- React Router for SPA routing.

**Main pages**

- `Landing` (`src/routes/Landing.tsx`)
  - Hero, tagline, CTA to preferences, and a mini preview of the recommendation logic.

- `Preference selection` (`src/routes/Preferences.tsx` + `components/PreferenceForm.tsx`)
  - Sliders for camera, battery, performance, storage, RAM priorities.
  - Budget slider (INR).
  - OS preference (Android / iOS).
  - Minimum RAM and storage filters.
  - Primary use (normal, gaming, photography).
  - On submit, calls `POST /recommend` and navigates to the results page.

- `Results` (`src/routes/Results.tsx`)
  - Shows the top recommendations as rich cards (`PhoneCard`).
  - Displays match percentage, key specs, tags, and &ldquo;Why this phone?&rdquo; explanations.
  - Sorting filters: by match, price ascending, price descending.
  - Let users mark phones to compare side by side.

- `Comparison` (`src/routes/Compare.tsx`)
  - Displays a side-by-side comparison table (`ComparisonTable`) using phones selected from results.

- `Admin` (`src/routes/Admin.tsx`)
  - Form to enter `API_SECRET_TOKEN` and trigger `/update-database`.
  - Shows current phone count using `GET /phones`.

**UI details**

- Dark/light mode toggling via `useTheme` hook and `ThemeToggle` component.
- Animated cards and buttons using Tailwind transitions and gradients.
- `LoadingSpinner` and `ErrorBanner` for loading and error states.

---

### 6. Environment Setup

#### 6.1. Backend / Scraper Python environment

1. **Create and activate a virtualenv** (recommended):

   ```bash
   cd "Personal Projects/Phone Selector"
   python -m venv .venv
   source .venv/bin/activate  # Linux/macOS
   # On Windows: .venv\Scripts\activate
   ```

2. **Install backend (and scraper) dependencies**:

   ```bash
   cd backend
   pip install -r requirements.txt
   cd ..
   ```

3. **Configure environment variables**:

   ```bash
   cd backend
   cp .env.example .env
   # Open .env and set:
   # MONGO_URI=<your MongoDB Atlas URI with user/password>
   # MONGO_DB=phone_recommender
   # PHONES_COLLECTION=phones
   # API_SECRET_TOKEN=<strong secret for admin endpoint>
   cd ..
   ```

   For your case, set `MONGO_URI` to the cluster URL you provided (do not commit the `.env` file).

#### 6.2. Frontend Node environment

1. Install Node.js (18+ recommended).

2. Install frontend dependencies:

   ```bash
   cd "Personal Projects/Phone Selector/frontend"
   npm install
   cd ..
   ```

3. (Optional) Create `frontend/.env` to override API base URL if needed:

   ```bash
   VITE_API_BASE_URL=http://localhost:8000
   ```

   By default the frontend uses `http://localhost:8000`.

---

### 7. How to Run Web Scraping

You have **two ways** to run the scraper: directly from the command line or via the admin API.

#### 7.1. Run scraper from the command line

From the project root:

```bash
cd "Personal Projects/Phone Selector"
source .venv/bin/activate        # if you created a virtualenv

# Ensure backend dependencies are installed (see above)

# Run the scraper (uses PYTHONPATH so it can import backend.app.db)
PYTHONPATH=. python -m scraper.scrape_phones
```

What happens:

- The scraper connects to your MongoDB using the `MONGO_URI` from `backend/.env`.
- It fetches up to ~150 devices from PhoneDB, parses specs, and upserts into the `phones` collection.
- On completion, it prints how many devices were successfully upserted.

You can run this periodically to keep your database fresh.

#### 7.2. Run scraper via the backend API

1. Make sure the backend server is running (see next section).
2. Call the admin endpoint with your secret token:

```bash
curl -X POST "http://localhost:8000/update-database?api_token=YOUR_API_SECRET_TOKEN"
```

This:

- Triggers `run_scraper()` on the server.
- Clears the in-memory recommendation cache.
- Returns JSON like:

```json
{ "status": "ok", "updated_count": 123 }
```

You can also trigger this from the **Admin** page in the frontend by entering the same `API_SECRET_TOKEN`.

---

### 8. How to Run the Backend and Frontend

#### 8.1. Start the backend (FastAPI)

From the project root:

```bash
cd "Personal Projects/Phone Selector"
source .venv/bin/activate   # if using virtualenv

PYTHONPATH=. uvicorn backend.app.main:app --reload --port 8000
```

Notes:

- `PYTHONPATH=.` allows the backend to import the `scraper` package.
- FastAPI interactive docs:
  - Swagger UI: `http://localhost:8000/docs`
  - ReDoc: `http://localhost:8000/redoc`

#### 8.2. Start the frontend (React + Vite)

In another terminal:

```bash
cd "Personal Projects/Phone Selector/frontend"
npm run dev
```

Open the app in your browser at:

- `http://localhost:5173`

The frontend is already configured with CORS to talk to `http://localhost:8000`.

---

### 9. Typical Workflow

1. **Configure MongoDB** in `backend/.env` (`MONGO_URI` etc.).
2. **Install dependencies** for backend and frontend.
3. **Run the scraper once** to fill the database:
   - Either via CLI: `PYTHONPATH=. python -m scraper.scrape_phones`
   - Or via API: `POST /update-database` (using the Admin page or curl).
4. **Start the backend** (`uvicorn backend.app.main:app --reload --port 8000`).
5. **Start the frontend** (`npm run dev` in `frontend/`).
6. Visit `http://localhost:5173` and:
   - Set your preferences, view recommendations and explanations.
   - Compare shortlisted phones.
   - Use the Admin page to refresh data as needed.

---

### 10. Production Considerations

- **Secrets**: Never commit `backend/.env` or your Atlas URI to source control.
- **Scheduling scraper**:
  - Use a cron job or a scheduler like systemd timer / GitHub Actions to run:

    ```bash
    cd /path/to/Phone\ Selector
    source .venv/bin/activate
    PYTHONPATH=. python -m scraper.scrape_phones
    ```

- **Caching**: For multi-instance deployments, replace in-memory cache with Redis or similar.
- **Auth**: Replace the simple token-based `/update-database` protection with proper authentication (JWT, session-based admin panel, etc.) if exposed beyond localhost.

