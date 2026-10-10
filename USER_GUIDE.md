# Dukaan Dost Dashboard: Simple User Guide

This guide explains how to open Dukaan Dost, prepare your shop's CSV, use each section, and understand the results.

## Before you sign in

The app owner must configure MongoDB Atlas before anyone can create an account:

1. Create a MongoDB Atlas project and cluster.
2. In **Database Access**, create a dedicated database user and strong password.
3. In **Network Access**, allow the deployed app to reach the cluster. Use the narrowest practical access rule; broad network access should only be paired with a dedicated, least-privilege user and a strong password.
4. In Streamlit Cloud, open the app's **Settings → Secrets** and set:

   ```toml
   MONGODB_URI = "mongodb+srv://<database-user>:<password>@<cluster-host>/?retryWrites=true&w=majority"
   MONGODB_DATABASE = "dukaan_dost"
   ```

   Replace all placeholders with the real Atlas connection details. If a password contains special characters, URL-encode it in the URI.
5. Save Secrets and reboot the app.

Never send the real URI/password in a screenshot, chat, README, or GitHub commit. For local development, place these variables in a private `.env` file at the project root. `.env.example` is only a placeholder template: the app does not load values from it.

## Create your account and sign in

1. Open the app. The sign-in page appears.
2. To explore the sample dashboard without an account, choose **Continue as guest with example data**. Guest uploads are temporary and cannot be saved to Atlas.
3. To use your own saved data, choose **Create account**, enter an email address, and set a password of at least 12 characters. Atlas must be configured by the app owner first.
4. Sign in with that email and password.
5. Use **Sign out** in the sidebar when finished.

Passwords are stored as a one-way password hash, not as readable text. At present, the app does not have a password-reset/email-verification flow, so use an email you control and keep your password safe.

## 1. What the dashboard does

The dashboard helps you explore sales records. It can show:

- Total sales and recorded profit
- Order counts and average order value
- Sales trends over time
- Region-wise sales and profit
- Product/category and customer-segment comparisons
- Discount-related summaries
- A downloadable CSV of the filtered records
- A PDF business summary
- Optional AI-written suggestions, when a Groq key is configured
- A rough order scenario estimate from the models included with the app

It is a decision-support/demo tool, not accounting software. Check your books and actual costs before making business decisions.

## 2. Start from the beginning

### Try the example data first

1. Open the live app or start it locally.
2. The app loads its example shop data automatically. You do not need to upload anything to explore it.
3. Choose a language using **Language / भाषा** in the sidebar.
4. Use the sidebar to move between **Shop overview**, **Orders & data**, **Try an order idea**, and **Shop summary**.
5. Open **Filters (optional)** if you want to view only certain dates, areas, product types, or customer types. Leave all choices selected to see all the data.

### Upload your own CSV

1. Export your shop's order or sales details from your billing/POS software as a **CSV** file. Excel workbooks (`.xlsx`) are not accepted directly; save/export the sheet as CSV first.
2. Compare its headings with the field list below. Use the exact column names shown, including spaces and capitalization.
3. Make sure the sales and profit columns contain numbers, not formatted text such as `₹1,25,000`.
4. In the sidebar, choose **Your data → Choose your shop's CSV file** and select the CSV.
5. The app shows the uploaded file name and number of rows. Use the optional filters to narrow the view.
6. To keep the CSV for your next visit, choose **Save uploaded CSV to my account**. This replaces your previously saved dataset.
7. On a later visit, sign into the same account. Your saved CSV is used automatically. Clear/remove a new upload to switch back to the saved copy.
8. Open **MongoDB Atlas** in the sidebar to see saved-file details or delete your saved CSV.

You can start with the small example file at [`data/shop_sales_template.csv`](data/shop_sales_template.csv). It contains fictional data; replace it with your own records before analysis.

## 3. Prepare your CSV

The app reads one row as one sale line/item. If a bill has multiple products, you may use multiple rows with the same `Order ID`; keep each row's sales and profit values for that item, and do not repeat the full bill total on every item row.

### Core columns

For the main sales and profit overview, include these two numeric columns:

| Column name | What to enter | Example |
|---|---|---:|
| `Sales` | The sales amount for that row, in rupees | `1250.00` |
| `Profit` | Profit for that row after the costs you have included | `250.00` |

The displayed currency is `₹`, but the app **does not convert currencies**. Enter rupee amounts if you want the totals to represent INR. Profit is only as complete as the costs accounted for in your source records; rent, wages, tax, delivery, or other expenses may be missing.

### Recommended columns

These make more dashboard features available:

| Column name | What to enter | Example / format | Used for |
|---|---|---|---|
| `Order ID` | Same unique bill/order number for all its item rows | `BILL-1001` | Counts distinct orders. If absent, each row is counted as an order. |
| `Order Date` | Date the customer placed the order | `2026-09-14` | Sales trend and date filter. Use a consistent date format; `YYYY-MM-DD` is recommended. |
| `Region` | Your shop area, branch, locality, city, or sales territory | `Pune West` | Area comparisons and region filter. |
| `Category` | Product group/type | `Groceries` | Product-type comparisons and filter. |
| `Quantity` | Number of units in that row | `2` | Order/product detail and scenario context. |
| `Discount` | Discount as a decimal fraction from 0 to 1 | `0.10` means 10%; `0` means no discount | Discount summaries and comparisons. Do not enter `10` for 10% in the CSV. |
| `Segment` | Customer group, if you already use one | `Retail` | Customer-type comparison and filter. |

### Other helpful optional columns

You may also include `Product Name`, `Sub-Category`, `Product ID`, `Customer ID`, `Customer Name`, `Ship Date`, and `Ship Mode`. `Product Name` enables the app to call out a product with a recorded loss. Customer names/IDs are not needed for the main charts; consider removing identifying information before uploading.

### Example CSV layout

```csv
Order ID,Order Date,Region,Category,Product Name,Sales,Profit,Quantity,Discount,Segment
BILL-1001,2026-09-14,Pune West,Groceries,Rice 5 kg,1250.00,180.00,1,0.05,Retail
BILL-1002,2026-09-14,Pune East,Household,Detergent,420.00,65.00,2,0.10,Retail
BILL-1003,2026-09-15,Nashik,Snacks,Biscuits,300.00,-20.00,3,0,Wholesale
```

Keep the heading row. Leave an unknown value blank rather than writing words such as `N/A` into a numeric column. Do not include thousands separators or currency symbols in numeric cells: use `1250.00`, not `₹1,250.00`.

## 4. What each section does

### 📊 Shop overview

- **Sales:** sum of the `Sales` column in the current filtered data.
- **Profit:** sum of `Profit`, based only on costs already reflected in your records.
- **Profit from every ₹100 in sales:** profit divided by sales. It can be negative if recorded profit is negative.
- **Orders:** number of unique `Order ID` values. Without that column, the app counts rows instead.
- Charts and tables compare sales/profit over dates, areas, and product types when those columns are available.
- The attention cards can show the least-profitable product type, a product with a loss, and average discount when the matching columns exist.

### 🔎 Orders & data

- Review uploaded order rows.
- Check how many cells are blank and how many rows are exact duplicates.
- Review column types and completeness.
- Download the currently filtered rows as a CSV.

The duplicate count identifies rows that match exactly; it does not decide whether two similar-looking bills are genuinely duplicates.

### 🧪 Try an order idea

Enter:

- **Number of items:** 1–100
- **Discount (%):** enter a whole percentage, e.g. `10` for 10%
- **Year** and **order month**

The app calculates the quarter and shows an estimated sales amount and whether profit looks likely. It also compares that scenario with a discount reduced by 10 percentage points (not less than 0%).

**Important:** this estimate uses the pre-trained model files bundled with the app. Uploading your CSV does not train or personalize those models. Treat the result as a rough demonstration, not a guaranteed sales/profit forecast or a substitute for checking costs.

### ✨ Shop summary

- Shows a short summary based on the current filters.
- **Download summary (PDF)** saves the displayed summary.
- **Get simple ideas from AI** asks Groq to suggest a few checks based on that summary. It is optional; the dashboard and PDF work without an API key.

When AI is used, the app sends the generated summary—not the full CSV—to Groq to prepare suggestions. The uploaded CSV is still sent to the server hosting this app for processing. Only upload data you are allowed to share with that service.

### 🗄️ MongoDB Atlas

- Shows whether the app reached its configured Atlas database.
- Shows the name, row count, columns, and save time of your saved CSV.
- Lets you delete your saved CSV from your account. Deletion cannot be undone.
- Saving a new upload replaces the previous saved dataset for that account.

The page does not reveal database credentials. Each dataset and row is queried with the signed-in account ID, so one account cannot select another account's saved rows through the app interface.

## 5. Filters, language, and currency

- Filters apply to the current uploaded/example data and affect charts, tables, and the report.
- Date filtering needs `Order Date`; area filtering needs `Region`; product filtering needs `Category`; customer-type filtering needs `Segment`.
- If a column is missing, the related filter or comparison may not appear.
- Choose a supported language in the sidebar. Some charts, headings, and instructions use the selected language.
- Amounts show the `₹` symbol and Indian digit grouping. This is display formatting only; the app does not convert USD or another currency into INR.

## 6. Common problems

| What you see | What to check |
|---|---|
| Dashboard asks for `Sales` and `Profit` | Add both columns with those exact headings and numeric values. |
| Date trend or date filter is missing | Add `Order Date` and use valid, consistent dates such as `2026-09-14`. |
| No area/product/customer comparison | Add `Region`, `Category`, or `Segment` respectively. |
| Amounts or percentages look unusually large | Remove currency symbols/commas; check that `Discount` is a fraction such as `0.10` (10%). |
| AI button is disabled | Add `GROQ_API_KEY` in Streamlit Cloud **App settings → Secrets** or your local `.env`, then restart/reboot the app. Keep the key private. |
| AI button is enabled but returns an error | Check the app logs, key validity/quota, network access, and that the app has restarted after changing Secrets. |
| PDF download fails for a translated report | Update/restart the deployed app to the latest version; the app bundles a fallback font for common Unicode/rupee text. |
| Forecast fails | Check the app logs and confirm the deployed repository includes the model files under `model/`. |

## 7. Run locally on Windows

From the project folder in PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m streamlit run app\app.py
```

If script activation is blocked, run this in the same PowerShell window and activate again:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
```

## 8. Keep your data and secrets safe

- In the hosted version, the selected CSV is uploaded to the Streamlit-hosted app server so it can be processed. Do not assume it is processed only in your browser.
- Choosing **Save uploaded CSV to my account** stores those sales rows in the MongoDB Atlas database configured by the app owner. Signing out does not delete saved data; use the MongoDB Atlas page's delete action for that.
- Do not upload sensitive customer, payment-card, password, or confidential business information to a public demo.
- AI is optional. If used, a short generated summary is sent to Groq; do not enable it for information you cannot share with that service.
- Keep the real `GROQ_API_KEY` in Streamlit Cloud **Secrets** or a private local `.env`. Never put a real key in a public CSV, README, screenshot, or GitHub commit.
- Keep the real `MONGODB_URI` in Streamlit Cloud **Secrets** or a private local `.env`. Anyone with this URI may be able to access the configured database.
