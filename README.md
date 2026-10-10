# AI-Powered Business Intelligence & Forecasting Platform

A shop-focused business intelligence dashboard built with Streamlit for small and medium businesses. It helps shopkeepers understand sales, profit, regional performance, discount impact, and forecast ideas using simple, friendly language and Indian currency formatting.

## Why this project matters

This app is designed for a real-world shop environment where owners may have different levels of technical comfort. The interface uses:

- Simple, visual KPI cards
- Plain-language explanations
- White/light theme for readability
- Indian rupee (`₹`) formatting with Indian number grouping
- Multiple Indian language options
- Region-wise business analysis
- Forecasting and summary PDF export

## Key features

- Overview dashboard with sales, profit, and order metrics
- Sales & profit trend analysis
- Region-wise performance summary
- Category and customer segmentation insights
- Discount sensitivity analysis
- Forecast for quantity, discount, and seasonal planning
- AI-powered summary tips when a valid Groq API key is configured
- PDF report export for shop summaries
- Language support for English and major Indian languages

## Tech stack

- Python 3.10+
- Streamlit
- Pandas
- NumPy
- scikit-learn
- Matplotlib
- ReportLab
- Groq API
- Joblib

## Repository structure

```text
AI-Powered Business Intelligence & Forecasting Platform/
├── app/
│   ├── app.py
│   ├── charts.py
│   ├── components.py
│   ├── config.py
│   ├── formatting.py
│   ├── translations.py
│   └── utils.py
├── data/
│   ├── cleaned/
│   │   ├── superstore_synthetic.csv
│   │   └── superstore_cleaned.csv
│   └── raw/
│       ├── superstore.csv
│       └── reviews.csv
├── model/
│   ├── sales_regression.pkl
│   ├── profit_classifier.pkl
│   ├── scaler.pkl
│   ├── sentiment_model.pkl
│   └── tfidf_vectorizer.pkl
├── notebooks/
│   └── 01_data_loading.ipynb
├── .streamlit/
│   └── config.toml
├── .env.example
├── .gitignore
├── requirements.txt
├── README.md
├── LICENSE
├── AI_Business_Report.pdf
├── package-lock.json
└── api key.txt
```

## Quick start

1. Clone the repository
2. Create and activate a virtual environment
3. Install dependencies
4. Run the app

```bash
python -m venv .venv
source .venv/bin/activate   # Linux/macOS
.venv\Scripts\activate      # Windows PowerShell

pip install -r requirements.txt
streamlit run app/app.py
```

## Local environment variables

Create a `.env` file in the project root using the example file.

```env
GROQ_API_KEY=your_api_key_here
```

Important:
- Do not commit `.env` to GitHub
- Keep API keys secure
- Store secrets only in your local environment or deployment platform secret manager

## Deployment guide

### Option 1: Streamlit Community Cloud

1. Push this repository to GitHub
2. Go to: https://streamlit.io/cloud
3. Sign in with GitHub
4. Create a new app
5. Connect the repository
6. Set the main file path to `app/app.py`
7. Add the environment variable:
   - `GROQ_API_KEY`
8. Deploy

### Option 2: Local deployment

```bash
streamlit run app/app.py
```

## Notes on data and privacy

This project was designed for shop analytics and uses a synthetic demo dataset for safe public sharing. If you upload your own business CSV file, the app processes it locally in your browser session.

- No upload is sent to the project repository
- AI suggestions require a valid Groq API key
- Public repos should use synthetic/demo data by default

## Documentation standards

This README is written to make the project understandable for a new developer, reviewer, or client. It includes:

- Project purpose
- Business use case
- Architecture overview
- Setup instructions
- Deployment instructions
- Data handling notes
- Security notes

## License

This project is distributed for educational and demo use. Add an appropriate open-source license if you want to publish it publicly.

## Future improvements

- Add authentication for admin access
- Add export to Excel + CSV
- Add more forecasting models
- Add chatbot with conversation memory
- Add monthly planning dashboard
- Add multi-tenant support for multiple stores

## Contact / project ownership

This project is prepared for demonstration and can be published as a portfolio or business startup sample.
