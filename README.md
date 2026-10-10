# AI-Powered Business Intelligence & Forecasting Platform

A shop-focused business intelligence dashboard built with Streamlit for small and medium businesses. It helps shopkeepers understand sales, profit, regional performance, discount impact, and forecast ideas using simple, friendly language and Indian currency formatting.

> **New here?** Start with the step-by-step [User Guide](USER_GUIDE.md) for CSV requirements, example data, every dashboard feature, and common questions.

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
- Email/password registration and login
- MongoDB Atlas storage for each user's saved sales CSV
- Guest access to the example dashboard without an account

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
│   ├── database.py
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
│   ├── shop_sales_template.csv
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
├── USER_GUIDE.md
├── LICENSE
├── package-lock.json
```

## Quick start

1. Clone the repository
2. Create and activate a virtual environment
3. Install dependencies
4. Run the app

```powershell
deactivate  # Run only if another virtual environment is currently active
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m streamlit run app\app.py
```

On Windows, run the app with Streamlit rather than `python app.py`: the entrypoint is `app\app.py`, and it uses Streamlit's runtime. If PowerShell blocks activation, allow it for the current terminal only with:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
```

Use either the existing `venv` or the new `.venv`; do not create/activate a virtual environment inside another active one. Make sure installation and launch use the same environment by using `python -m pip` and `python -m streamlit`.

## Local environment variables

Create a `.env` file in the project root using `.env.example` as a template. Replace the sample values; do not commit the real `.env`.

```env
GROQ_API_KEY=your_groq_api_key_here
MONGODB_URI=mongodb+srv://username:password@cluster0.example.mongodb.net/?retryWrites=true&w=majority
MONGODB_DATABASE=dukaan_dost
```

Important:
- Do not commit `.env` to GitHub
- Keep API keys secure
- Store secrets only in your local environment or deployment platform secret manager
- The MongoDB URI contains a database password. URL-encode special characters in the password.

## MongoDB Atlas setup

Accounts and saved datasets require a reachable MongoDB Atlas cluster:

1. Create an Atlas project and a database cluster.
2. Create a dedicated database user with a strong password. Do not use your Atlas website login as the database user.
3. Configure the Atlas network access list to allow connections from the deployment. Restrict access where possible; if broad access is required by the hosting platform, use a dedicated least-privilege database user and a strong password.
4. Copy the cluster's `mongodb+srv://` connection string and replace its username/password placeholders.
5. Set `MONGODB_URI` and `MONGODB_DATABASE` in your local `.env` or Streamlit Cloud app secrets.
6. Restart/reboot the app after changing secrets. The app checks the connection and creates its indexes automatically.

Streamlit Cloud **App settings → Secrets** example:

```toml
MONGODB_URI = "mongodb+srv://<database-user>:<password>@<cluster-host>/?retryWrites=true&w=majority"
MONGODB_DATABASE = "dukaan_dost"
GROQ_API_KEY = "your_groq_api_key_here"
```

Replace the example values before saving. Keep this information private. The app hashes passwords with PBKDF2-HMAC-SHA256; it does not store raw account passwords. Each saved row and dataset is scoped to the signed-in account. Users can replace or delete their saved dataset from the MongoDB Atlas page inside the app.

The hosted dashboard requires MongoDB Atlas to be configured before users can sign in. If no Atlas URI is configured, it shows setup instructions instead of opening the protected dashboard.

## Deployment guide

### Option 1: Streamlit Community Cloud

1. Push this repository to GitHub
2. Go to: https://streamlit.io/cloud
3. Sign in with GitHub
4. Create a new app
5. Connect the repository
6. Set the main file path to `app/app.py`
7. Open **App settings → Secrets** and add:

   ```toml
   MONGODB_URI = "mongodb+srv://<database-user>:<password>@<cluster-host>/?retryWrites=true&w=majority"
   MONGODB_DATABASE = "dukaan_dost"
   GROQ_API_KEY = "your_groq_api_key_here"
   ```

8. Deploy

AI suggestions are optional. The rest of the dashboard works without this key. Never publish the real key in GitHub or screenshots.

### Option 2: Local deployment

```bash
streamlit run app/app.py
```

## Notes on data and privacy

This project was designed for shop analytics and uses a synthetic demo dataset for safe public sharing. If you upload your own business CSV file to the hosted app, it is sent to the Streamlit app server for processing; it is not processed only in your browser. When you explicitly save it, its rows are stored in your configured MongoDB Atlas database. See the [User Guide](USER_GUIDE.md) for details about data handling.

- Uploaded data is not sent to the GitHub repository, but the hosted app server processes it
- Saved data is stored in the MongoDB Atlas database configured by the app owner
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
