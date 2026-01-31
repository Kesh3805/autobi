<div align="center">

# 🚀 AutoBI

### *LLM-Powered Data Explorer*

[![Next.js](https://img.shields.io/badge/Next.js-14-black?style=for-the-badge&logo=next.js)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-009688?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![DuckDB](https://img.shields.io/badge/DuckDB-0.10-FFF000?style=for-the-badge)](https://duckdb.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.3-3178C6?style=for-the-badge&logo=typescript)](https://www.typescriptlang.org/)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python)](https://python.org/)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

<br />

**Upload a CSV → Get Dashboards → Ask Questions in Plain English**

<br />

[✨ Features](#-features) •
[🛠️ Tech Stack](#️-tech-stack) •
[🚀 Quick Start](#-quick-start) •
[📖 API Reference](#-api-reference) •
[🎨 Screenshots](#-screenshots)

---

<br />

</div>

## ✨ Features

<table>
<tr>
<td width="50%">

### 🧠 Natural Language to SQL
- Schema-grounded query generation
- DuckDB-compatible SQL with CTEs
- Safety validation (read-only enforcement)
- Confidence scoring with stated assumptions
- **Rule-based fallback** when LLM unavailable

</td>
<td width="50%">

### 📊 Smart Visualizations
- Intent-aware chart selection
- 📈 Line charts for trends
- 📊 Bar charts for comparisons
- 🍩 Doughnut/Pie for compositions
- 📉 Histograms for distributions
- ⚡ Scatter plots for correlations

</td>
</tr>
<tr>
<td width="50%">

### 💡 Intelligent Insights
Auto-detected patterns with:
- **Observation**: What changed?
- **Magnitude**: How much?
- **Baseline**: Compared to what?
- **Confidence**: Data coverage / volatility

</td>
<td width="50%">

### 🎨 Modern UI/UX
- 🌙 **Dark Mode** with system detection
- 📜 Query history with replay
- 📥 Export to CSV/JSON/Clipboard
- ⏳ Smooth loading skeletons
- 🔍 Smart autocomplete suggestions

</td>
</tr>
</table>

<br />

## 🛠️ Tech Stack

<div align="center">

| Frontend | Backend | Database | AI/ML |
|:--------:|:-------:|:--------:|:-----:|
| ![Next.js](https://img.shields.io/badge/-Next.js_14-000?style=flat-square&logo=next.js) | ![FastAPI](https://img.shields.io/badge/-FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white) | ![DuckDB](https://img.shields.io/badge/-DuckDB-FFF000?style=flat-square) | ![OpenAI](https://img.shields.io/badge/-OpenAI-412991?style=flat-square&logo=openai&logoColor=white) |
| ![React](https://img.shields.io/badge/-React_18-61DAFB?style=flat-square&logo=react&logoColor=black) | ![Python](https://img.shields.io/badge/-Python_3.10+-3776AB?style=flat-square&logo=python&logoColor=white) | ![SQL](https://img.shields.io/badge/-SQL-4479A1?style=flat-square&logo=postgresql&logoColor=white) | ![LangChain](https://img.shields.io/badge/-LangChain-121212?style=flat-square) |
| ![TailwindCSS](https://img.shields.io/badge/-Tailwind_CSS-06B6D4?style=flat-square&logo=tailwindcss&logoColor=white) | ![Pydantic](https://img.shields.io/badge/-Pydantic-E92063?style=flat-square&logo=pydantic&logoColor=white) | | |
| ![Chart.js](https://img.shields.io/badge/-Chart.js-FF6384?style=flat-square&logo=chartdotjs&logoColor=white) | | | |

</div>

<br />

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              User Interface                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │ File Upload │  │Query Input  │  │ Schema View │  │ Results Dashboard   │ │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────────┬──────────┘ │
└─────────┼────────────────┼────────────────┼────────────────────┼────────────┘
          │                │                │                    │
          ▼                ▼                ▼                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           FastAPI Backend                                    │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                        Request Router                                 │   │
│  └─────────┬──────────────────┬──────────────────┬──────────────────────┘   │
│            │                  │                  │                          │
│  ┌─────────▼────────┐ ┌───────▼───────┐ ┌───────▼───────┐                   │
│  │  Query Engine    │ │ Insight Engine│ │ Chart Selector│                   │
│  │  ┌────────────┐  │ │               │ │               │                   │
│  │  │ LLM (GPT)  │  │ │ Stats & Trend │ │ Intent-aware  │                   │
│  │  │     OR     │  │ │  Detection    │ │  Selection    │                   │
│  │  │ Rule-based │  │ │               │ │               │                   │
│  │  └────────────┘  │ └───────────────┘ └───────────────┘                   │
│  └─────────┬────────┘                                                       │
│            │                                                                 │
│  ┌─────────▼────────────────────────────────────────────────────────────┐   │
│  │                         DuckDB Engine                                 │   │
│  │  • In-memory analytics  • CSV ingestion  • SQL execution              │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

<br />

## 🚀 Quick Start

### Prerequisites

- 🐍 Python 3.10+
- 📦 Node.js 18+
- 🔑 OpenAI API key *(optional - falls back to rule-based SQL)*

### 1️⃣ Clone & Setup Backend

```bash
# Clone the repository
git clone https://github.com/yourusername/autobi.git
cd autobi

# Setup Python environment
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# (Optional) Configure OpenAI
copy .env.example .env
# Edit .env and add your OPENAI_API_KEY

# Start backend server
uvicorn app.main:app --reload --port 8000
```

### 2️⃣ Setup Frontend

```bash
# In a new terminal
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

### 3️⃣ Open & Explore! 🎉

| Service | URL |
|---------|-----|
| 🌐 Frontend | [http://localhost:3000](http://localhost:3000) |
| 🔧 Backend API | [http://localhost:8000](http://localhost:8000) |
| 📚 API Docs | [http://localhost:8000/docs](http://localhost:8000/docs) |

<br />

## 📖 API Reference

<details>
<summary><b>📤 POST /upload</b> - Upload CSV file</summary>

Upload a CSV file to create a new table.

**Request:** `multipart/form-data` with `file` field

**Response:**
```json
{
  "success": true,
  "table_name": "sales_data",
  "row_count": 1500,
  "profile": { ... }
}
```
</details>

<details>
<summary><b>📋 GET /tables</b> - List all tables</summary>

**Response:**
```json
{
  "tables": [
    { "name": "sales_data", "columns": [...], "row_count": 1500 }
  ]
}
```
</details>

<details>
<summary><b>🔍 GET /schema/{table}</b> - Get table schema</summary>

**Response:**
```json
{
  "columns": [
    { "name": "revenue", "type": "measure", "sample_values": [...] }
  ],
  "quality_score": 0.95
}
```
</details>

<details>
<summary><b>💬 POST /query</b> - Natural language query</summary>

**Request:**
```json
{
  "question": "Show total sales by category",
  "table_name": "sales_data"
}
```

**Response:**
```json
{
  "sql": "SELECT category, SUM(sales) AS total_sales FROM sales_data GROUP BY category",
  "data": [...],
  "columns": [...],
  "chart_recommendation": { "chart_type": "bar", ... },
  "insights": [...],
  "confidence": 0.92
}
```
</details>

<details>
<summary><b>📊 GET /sample/{table}</b> - Preview sample data</summary>
</details>

<details>
<summary><b>📈 GET /stats/{table}</b> - Get table statistics</summary>
</details>

<details>
<summary><b>💡 GET /suggestions/{table}</b> - Smart query suggestions</summary>
</details>

<details>
<summary><b>🗑️ DELETE /table/{table}</b> - Delete a table</summary>
</details>

<br />

## 🎨 Screenshots

<div align="center">

### 📊 Dashboard View
*Upload CSV, explore schema, ask questions*

### 🌙 Dark Mode
*Beautiful dark theme with system preference detection*

### 📈 Smart Charts
*Auto-selected visualizations based on your query intent*

</div>

<br />

## 💡 Query Examples

```
📊 "Show total sales by category"
📈 "What is the trend over time?"
🏆 "Top 10 customers by revenue"
📅 "Average order value by month"
📉 "Distribution of prices"
🆚 "Compare regions by profit"
🔻 "Bottom 5 performing products"
📊 "Share of revenue by segment"
```

<br />

## 🎯 Design Principles

| Principle | Description |
|-----------|-------------|
| 🎯 **Deterministic over Generative** | Prefer computation over generation |
| 🔒 **Data as Untrusted Input** | Validate every claim |
| 📊 **Quantify or Refuse** | Numbers beat adjectives |
| 💬 **State Assumptions** | Transparency over confidence |
| 📉 **Right Chart, Not Flashy** | One chart = one message |
| 🤫 **Silence When No Signal** | Don't invent patterns |

<br />

## 📁 Project Structure

```
AutoBI/
├── 📂 backend/
│   ├── 📂 app/
│   │   ├── 🐍 main.py              # FastAPI application
│   │   ├── 🐍 database.py          # DuckDB manager
│   │   ├── 🐍 schema_profiler.py   # Data profiling
│   │   ├── 🐍 query_engine.py      # NL→SQL conversion
│   │   ├── 🐍 insight_engine.py    # Pattern detection
│   │   └── 🐍 chart_selector.py    # Visualization logic
│   ├── 📄 requirements.txt
│   └── 📄 .env.example
│
├── 📂 frontend/
│   ├── 📂 src/
│   │   ├── 📂 app/
│   │   │   ├── ⚛️ layout.tsx
│   │   │   ├── ⚛️ page.tsx
│   │   │   └── 🎨 globals.css
│   │   ├── 📂 components/
│   │   │   ├── ⚛️ FileUpload.tsx
│   │   │   ├── ⚛️ QueryInterface.tsx
│   │   │   ├── ⚛️ ChartPanel.tsx
│   │   │   ├── ⚛️ DataTable.tsx
│   │   │   ├── ⚛️ QueryHistory.tsx
│   │   │   ├── ⚛️ ExportButton.tsx
│   │   │   └── ⚛️ ThemeToggle.tsx
│   │   └── 📂 context/
│   │       └── ⚛️ ThemeContext.tsx
│   ├── 📄 package.json
│   └── 📄 tailwind.config.js
│
└── 📄 README.md
```

<br />

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

<br />

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

<br />

---

<div align="center">

**Built with ❤️ using Next.js, FastAPI, and DuckDB**

⭐ Star this repo if you find it useful!

</div>
