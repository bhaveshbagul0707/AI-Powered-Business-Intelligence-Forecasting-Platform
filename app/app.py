from __future__ import annotations

from html import escape
from io import BytesIO

import joblib
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

import charts
from components import hero, inject_theme, kpi_row, section_header
from config import CONFIG, ROOT_DIR
from database import (
    AccountNotFoundError,
    AtlasNotConfiguredError,
    DatasetCleanupError,
    DatasetValidationError,
    EmailAlreadyRegisteredError,
    InvalidCredentialsError,
    authenticate_user,
    delete_active_dataset,
    get_active_dataset_metadata,
    get_database,
    get_user,
    load_sales_dataset,
    register_user,
    save_sales_dataset,
)
from formatting import indian_currency, indian_number
from pymongo.errors import PyMongoError
from translations import LANGUAGES, month_names, report_tips, translate as tr
from utils import ask_genai, generate_pdf


st.set_page_config(
    page_title=CONFIG.page_title,
    page_icon=CONFIG.page_icon,
    layout=CONFIG.layout,
    initial_sidebar_state="expanded",
)
inject_theme()


@st.cache_data(show_spinner=False)
def load_default_data() -> pd.DataFrame:
    candidates = [
        ROOT_DIR / "data" / "cleaned" / "superstore_synthetic.csv",
        ROOT_DIR / "data" / "cleaned" / "superstore_cleaned.csv",
    ]
    for path in candidates:
        if path.is_file():
            return pd.read_csv(path, encoding="ISO-8859-1")
    raise FileNotFoundError(f"Default dataset not found in: {candidates}")


@st.cache_data(show_spinner=False)
def parse_uploaded_data(contents: bytes) -> pd.DataFrame:
    try:
        return pd.read_csv(BytesIO(contents), encoding="utf-8-sig", low_memory=False)
    except UnicodeDecodeError:
        return pd.read_csv(BytesIO(contents), encoding="ISO-8859-1", low_memory=False)


@st.cache_resource(show_spinner=False)
def load_models():
    return (
        joblib.load(CONFIG.reg_model_path),
        joblib.load(CONFIG.clf_model_path),
        joblib.load(CONFIG.scaler_path),
    )


@st.cache_data(show_spinner=False)
def pdf_bytes(report: str, title: str) -> bytes:
    return generate_pdf(report, title=title).read_bytes()


def normalize_data(frame: pd.DataFrame) -> pd.DataFrame:
    data = frame.copy()
    data.columns = data.columns.astype(str).str.strip()
    for column in ("Sales", "Profit", "Quantity", "Discount"):
        if column in data:
            data[column] = pd.to_numeric(data[column], errors="coerce")
    for column in ("Order Date", "Ship Date"):
        if column in data:
            data[column] = pd.to_datetime(data[column], errors="coerce")
    return data


def currency(value: float) -> str:
    return indian_currency(value)


def show_chart(figure) -> None:
    if figure is not None:
        st.pyplot(figure, width="stretch")
        plt.close(figure)


def render_auth_page() -> None:
    st.markdown(
        "<div style='max-width:680px;margin:5vh auto 0'>",
        unsafe_allow_html=True,
    )
    st.title("🛍️ Dukaan Dost")
    st.subheader("Your shop's numbers, made easier.")
    st.write("Sign in to keep your shop data private to your account.")
    if st.button("Continue as guest with example data", width="stretch"):
        st.session_state["guest_mode"] = True
        st.rerun()
    if not CONFIG.mongodb_uri:
        st.info(
            "Guest demo is ready. To create accounts and save private shop data, "
            "the app owner must configure MongoDB Atlas first."
        )
        st.caption(
            "For local use, put MONGODB_URI in the project-root .env file. "
            "For Streamlit Cloud, add it under App settings → Secrets. "
            ".env.example is only a template and is not loaded."
        )
    login_tab, signup_tab = st.tabs(["Sign in", "Create account"])

    with login_tab:
        with st.form("login_form"):
            email = st.text_input("Email", autocomplete="email")
            password = st.text_input(
                "Password",
                type="password",
                autocomplete="current-password",
                max_chars=128,
            )
            submitted = st.form_submit_button("Sign in", width="stretch")
        if submitted:
            try:
                user = authenticate_user(email, password)
            except ValueError as exc:
                st.error(str(exc))
            except AtlasNotConfiguredError:
                st.error(
                    "MongoDB Atlas is not configured. The project .env.example is "
                    "only a template: set MONGODB_URI in local .env or Streamlit "
                    "Cloud → App settings → Secrets, then restart/reboot the app."
                )
            except PyMongoError:
                st.error("Could not sign in right now. Check the Atlas setup and app logs.")
            else:
                st.session_state["authenticated_user"] = user
                st.rerun()

    with signup_tab:
        st.caption("Use an email you can access. Password must be at least 12 characters.")
        with st.form("signup_form"):
            email = st.text_input("Email address", autocomplete="email", key="signup_email")
            password = st.text_input(
                "Create password",
                type="password",
                autocomplete="new-password",
                max_chars=128,
                key="signup_password",
            )
            confirmation = st.text_input(
                "Confirm password",
                type="password",
                autocomplete="new-password",
                max_chars=128,
                key="signup_confirmation",
            )
            submitted = st.form_submit_button("Create account", width="stretch")
        if submitted:
            if password != confirmation:
                st.error("The passwords do not match.")
            else:
                try:
                    user = register_user(email, password)
                except (ValueError, EmailAlreadyRegisteredError) as exc:
                    st.error(str(exc))
                except AtlasNotConfiguredError:
                    st.error(
                        "MongoDB Atlas is not configured. The project .env.example is "
                        "only a template: set MONGODB_URI in local .env or Streamlit "
                        "Cloud → App settings → Secrets, then restart/reboot the app."
                    )
                except PyMongoError:
                    st.error("Could not create the account. Check the Atlas setup and app logs.")
                else:
                    st.session_state["authenticated_user"] = user
                    st.success("Account created.")
                    st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)


def require_atlas() -> bool:
    try:
        get_database()
    except AtlasNotConfiguredError:
        st.error("MongoDB Atlas is not configured for this app.")
        st.markdown(
            "Add `MONGODB_URI` to Streamlit Cloud → **App settings → Secrets** "
            "and set `MONGODB_DATABASE = \"dukaan_dost\"`, then reboot the app."
        )
        st.code(
            'MONGODB_URI = "mongodb+srv://<database-user>:<password>@<cluster-host>/?retryWrites=true&w=majority"\n'
            'MONGODB_DATABASE = "dukaan_dost"',
            language="toml",
        )
        st.caption(
            "Create an Atlas database user, allow the Streamlit app to reach the cluster, "
            "and never commit the real connection string to GitHub."
        )
        return False
    except PyMongoError:
        st.error(
            "Could not connect to MongoDB Atlas. Check the connection string, database "
            "user/password, Atlas network access rules, and app logs."
        )
        return False
    return True


def render_sidebar(
    data: pd.DataFrame, user: dict[str, str] | None
) -> tuple[str, pd.DataFrame, str, dict | None]:
    if user is not None:
        if st.sidebar.button(f"Sign out · {user['email']}", width="stretch"):
            st.session_state.clear()
            st.rerun()
    else:
        st.sidebar.caption("Guest demo · example data only")
        if st.sidebar.button("Sign in or create account", width="stretch"):
            st.session_state.pop("guest_mode", None)
            st.rerun()

    language_options = list(LANGUAGES)
    current_language = st.session_state.get("language_choice", "English")
    if current_language not in language_options:
        current_language = "English"
    language = st.sidebar.selectbox(
        tr(current_language, "language"),
        language_options,
        index=language_options.index(current_language),
        key="language_choice",
        help=tr(current_language, "language_help"),
    )
    st.sidebar.markdown("## 🛍️ Dukaan Dost")
    st.sidebar.caption(tr(language, "workspace"))
    pages = ["overview", "explore", "forecast", "reports"]
    if user is not None:
        pages.append("database")
    page = st.sidebar.radio(
        tr(language, "workspace"),
        pages,
        format_func=lambda key: tr(language, key),
        label_visibility="collapsed",
        key="nav_page",
    )
    st.sidebar.divider()
    st.sidebar.markdown(f"#### {tr(language, 'data_source')}")
    saved_dataset = None
    if user is not None:
        try:
            saved_dataset = load_sales_dataset(user["id"])
        except (AccountNotFoundError, DatasetValidationError) as exc:
            st.sidebar.error(str(exc))
        except PyMongoError:
            st.sidebar.error("Could not load your saved shop data. Check the app logs.")

    if saved_dataset is not None:
        saved_frame, saved_metadata = saved_dataset
        use_saved = st.sidebar.checkbox("Use my saved data", value=True)
        if use_saved:
            data = saved_frame
            data_source = saved_metadata["file_name"]
        else:
            data_source = tr(language, "sample")
            data = load_default_data()
    else:
        saved_metadata = None
        data_source = tr(language, "sample")
        data = load_default_data()

    upload = st.sidebar.file_uploader(
        tr(language, "upload"),
        type=["csv"],
        help=tr(language, "upload_help"),
    )
    if upload is not None:
        try:
            data = parse_uploaded_data(upload.getvalue())
            data_source = upload.name
        except (UnicodeDecodeError, pd.errors.ParserError, ValueError) as exc:
            st.sidebar.error(tr(language, "csv_error", error=exc))
            upload = None
    data = normalize_data(data)
    st.sidebar.text(tr(language, "showing", source=data_source, count=indian_number(len(data))))
    missing_required = [column for column in ("Sales", "Profit") if column not in data]
    if missing_required and upload is not None:
        st.sidebar.warning(
            f"Add these required columns before saving: {', '.join(missing_required)}."
        )
    if upload is not None and user is not None:
        if st.sidebar.button(
            "💾 Save uploaded CSV to my account",
            disabled=bool(missing_required) or data.empty,
            width="stretch",
        ):
            try:
                metadata = save_sales_dataset(user["id"], data, upload.name)
            except (
                AccountNotFoundError,
                DatasetCleanupError,
                DatasetValidationError,
                ValueError,
            ) as exc:
                st.sidebar.error(str(exc))
            except PyMongoError:
                st.sidebar.error("Could not save the CSV to Atlas. Check the app logs.")
            else:
                st.sidebar.success(
                    f"Saved {metadata['row_count']:,} rows to your account. "
                    "Clear the upload to use the saved copy."
                )
    elif upload is not None:
        st.sidebar.caption("Guest uploads are temporary and are not saved.")

    filtered = data
    with st.sidebar.expander(tr(language, "filters"), expanded=False):
        st.caption(tr(language, "filter_help"))
        if "Order Date" in data.columns:
            dates = data["Order Date"].dropna()
            if not dates.empty:
                start, end = dates.min().date(), dates.max().date()
                chosen = st.date_input(
                    tr(language, "dates"),
                    value=(start, end),
                    min_value=start,
                    max_value=end,
                    key=f"date_{start}_{end}",
                    help=tr(language, "filter_help"),
                )
                if isinstance(chosen, (tuple, list)) and len(chosen) == 2:
                    lower, upper = pd.Timestamp(chosen[0]), pd.Timestamp(chosen[1]) + pd.Timedelta(days=1)
                    filtered = filtered[filtered["Order Date"].ge(lower) & filtered["Order Date"].lt(upper)]

        for column, key in (("Region", "region"), ("Category", "category"), ("Segment", "customer")):
            if column in data.columns:
                options = sorted(data[column].dropna().astype(str).unique().tolist())
                selected = st.multiselect(
                    tr(language, key),
                    options,
                    default=options,
                    key=f"filter_{column}_{hash(tuple(options))}",
                    help=tr(language, "filter_help"),
                )
                if selected:
                    filtered = filtered[filtered[column].astype(str).isin(selected)]
    st.sidebar.divider()
    st.sidebar.caption(tr(language, "footer"))
    st.sidebar.caption(tr(language, "currency_notice"))
    return page, filtered, language, saved_metadata


def database_page(user: dict[str, str], saved_metadata: dict | None) -> None:
    hero(
        "MongoDB Atlas & your saved data",
        "Your account's saved shop CSV is kept separately from other accounts.",
        "database",
    )
    st.success("MongoDB Atlas is connected for this session.")
    st.caption(f"Signed in as {user['email']}. Connection credentials are never shown here.")

    if saved_metadata is None:
        st.info("You do not have a saved CSV yet. Upload one in the sidebar and choose “Save uploaded CSV to my account”.")
        return

    st.markdown(f"**Saved file:** {saved_metadata['file_name']}")
    st.markdown(f"**Rows:** {indian_number(saved_metadata['row_count'])}")
    st.markdown(f"**Columns:** {', '.join(saved_metadata['columns'])}")
    uploaded_at = saved_metadata.get("uploaded_at")
    if uploaded_at is not None:
        st.markdown(f"**Saved at:** {uploaded_at.strftime('%Y-%m-%d %H:%M UTC')}")
    st.warning("Saving a new CSV replaces your currently saved dataset. Deleting it cannot be undone.")
    if st.button("🗑️ Delete my saved CSV", type="secondary"):
        try:
            delete_active_dataset(user["id"])
        except (AccountNotFoundError, PyMongoError):
            st.error("Could not delete the saved dataset. Check the app logs.")
        else:
            st.success("Your saved CSV was deleted.")
            st.rerun()


def executive_summary(data: pd.DataFrame, language: str = "English") -> str:
    sales = float(data["Sales"].sum()) if "Sales" in data else 0.0
    profit = float(data["Profit"].sum()) if "Profit" in data else 0.0
    margin = profit / sales if sales else 0.0
    lines = [
        tr(language, "your_summary"),
        f"{tr(language, 'rows')}: {indian_number(len(data))}",
        f"{tr(language, 'sales')}: {currency(sales)}",
        f"{tr(language, 'profit')}: {currency(profit)}",
        f"{tr(language, 'profit_rate')}: {indian_currency(margin * 100, 2)}",
    ]
    if {"Category", "Sales"}.issubset(data.columns) and not data.empty:
        category_sales = data.groupby("Category", observed=True)["Sales"].sum()
        lines.append(tr(language, "leading_category", name=category_sales.idxmax(), amount=currency(category_sales.max())))
    if {"Region", "Profit"}.issubset(data.columns) and not data.empty:
        region_profit = data.groupby("Region", observed=True)["Profit"].sum()
        lines.append(tr(language, "top_region", name=region_profit.idxmax(), amount=currency(region_profit.max())))
        if region_profit.min() < 0:
            lines.append(tr(language, "loss_region", name=region_profit.idxmin(), amount=currency(region_profit.min())))
    if "Order Date" in data.columns:
        valid_dates = data["Order Date"].dropna()
        if not valid_dates.empty:
            months = month_names(language)
            start = valid_dates.min()
            end = valid_dates.max()
            lines.append(
                tr(
                    language,
                    "period",
                    start=f"{months[start.month - 1]} {start.year}",
                    end=f"{months[end.month - 1]} {end.year}",
                )
            )
    lines.extend(
        [
            "",
            tr(language, "attention"),
            *[f"{index}. {tip}" for index, tip in enumerate(report_tips(language), start=1)],
        ]
    )
    return "\n".join(lines)


def overview_page(data: pd.DataFrame, language: str) -> None:
    hero(tr(language, "shop_title"), tr(language, "shop_subtitle"), tr(language, "overview"))
    if data.empty:
        st.warning(tr(language, "no_orders"))
        return
    missing_measures = [column for column in ("Sales", "Profit") if column not in data.columns]
    if missing_measures:
        st.error(tr(language, "required_columns", columns=", ".join(missing_measures)))
        return

    sales = float(data["Sales"].sum())
    profit = float(data["Profit"].sum())
    margin = profit / sales if sales else 0.0
    order_count = int(data["Order ID"].nunique()) if "Order ID" in data else len(data)
    average_order = sales / order_count if order_count else 0.0
    kpi_row(
        [
            {"icon": "💰", "label": tr(language, "sales"), "value": currency(sales), "note": tr(language, "sales_note")},
            {"icon": "💵", "label": tr(language, "profit"), "value": currency(profit), "note": tr(language, "profit_note")},
            {"icon": "🎯", "label": tr(language, "profit_rate"), "value": indian_currency(margin * 100, 2), "note": tr(language, "profit_rate_note")},
            {"icon": "📦", "label": tr(language, "orders"), "value": indian_number(order_count), "note": tr(language, "typical_order", amount=currency(average_order))},
        ]
    )
    st.write("")
    if profit > 0:
        st.success(tr(language, "good_news", sales=currency(sales), profit=currency(profit)))
    elif profit < 0:
        st.warning(tr(language, "loss_news", loss=currency(abs(profit))))
    else:
        st.info(tr(language, "meaning"))
    with st.expander(tr(language, "meaning")):
        st.markdown(
            f"- **{tr(language, 'sales')}:** {tr(language, 'sales_meaning')}\n"
            f"- **{tr(language, 'profit')}:** {tr(language, 'profit_meaning')}\n"
            f"- **{tr(language, 'profit_rate')}:** {tr(language, 'rate_meaning')}\n"
            f"- **{tr(language, 'orders')}:** {tr(language, 'orders_meaning')}"
        )

    section_header(tr(language, "performance"), tr(language, "performance_note"))
    trend = charts.sales_trend(data, language)
    left, right = st.columns([1.55, 1])
    with left:
        show_chart(trend)
        if trend is None:
            st.info(tr(language, "date_trend_missing"))
    with right:
        show_chart(charts.profit_by_region(data, language))
        if "Region" not in data or data.empty:
            st.info(tr(language, "no_region"))

    if {"Region", "Sales", "Profit"}.issubset(data.columns):
        section_header(tr(language, "region_breakdown"), tr(language, "region_note"))
        grouped = data.groupby("Region", dropna=False, observed=True)
        region_table = grouped.agg(Sales=("Sales", "sum"), Profit=("Profit", "sum"))
        if "Order ID" in data.columns:
            region_table[tr(language, "orders")] = grouped["Order ID"].nunique()
        else:
            region_table[tr(language, "orders")] = grouped.size()
        margin_label = tr(language, "profit_rate")
        region_table[margin_label] = (
            region_table["Profit"].div(region_table["Sales"].where(region_table["Sales"].ne(0))).fillna(0)
        )
        region_table = region_table.sort_values("Sales", ascending=False).reset_index()
        region_table["Region"] = region_table["Region"].fillna("—")
        region_table = region_table.rename(
            columns={
                "Region": tr(language, "region"),
                "Sales": tr(language, "sales"),
                "Profit": tr(language, "profit"),
            }
        )
        region_table[tr(language, "sales")] = region_table[tr(language, "sales")].map(currency)
        region_table[tr(language, "profit")] = region_table[tr(language, "profit")].map(currency)
        region_table[margin_label] = region_table[margin_label].map(
            lambda rate: indian_currency(rate * 100, 2)
        )
        st.dataframe(region_table, width="stretch", hide_index=True)

    left, right = st.columns(2)
    with left:
        show_chart(charts.sales_by_category(data, language))
        if "Category" not in data:
            st.info(tr(language, "no_category"))
    with right:
        show_chart(charts.segment_pie(data, language))
        if "Segment" not in data:
            show_chart(charts.discount_profitability(data, language))
            if "Discount" not in data:
                st.info(tr(language, "no_mix"))

    section_header(tr(language, "attention"), tr(language, "performance_note"))
    insights = []
    if {"Category", "Profit"}.issubset(data.columns) and not data.empty:
        category_profit = data.groupby("Category", observed=True)["Profit"].sum()
        worst = category_profit.idxmin()
        insights.append((tr(language, "profit_category"), str(worst), currency(float(category_profit.min()))))
    if {"Product Name", "Profit"}.issubset(data.columns) and not data.empty:
        product_profit = data.groupby("Product Name", observed=True)["Profit"].sum().sort_values()
        losses = product_profit[product_profit < 0].head(1)
        if not losses.empty:
            insights.append((tr(language, "loss_product"), str(losses.index[0]), currency(float(losses.iloc[0]))))
    if "Discount" in data.columns:
        insights.append((tr(language, "average_discount"), f"{data['Discount'].mean():.1%}", tr(language, "price_reduction")))
    if insights:
        for offset in range(0, len(insights), 2):
            row = insights[offset:offset + 2]
            cols = st.columns(2)
            for col, (label, value, note) in zip(cols, row):
                with col:
                    st.markdown(
                        f'<div class="panel"><div class="eyebrow">{escape(label)}</div><h3 class="signal-value">{escape(value)}</h3><span style="color:#64748b">{escape(note)}</span></div>',
                        unsafe_allow_html=True,
                    )
    else:
        st.info(tr(language, "no_mix"))


def explore_page(data: pd.DataFrame, language: str) -> None:
    hero(tr(language, "explore_title"), tr(language, "explore_subtitle"), tr(language, "explore"))
    if data.empty:
        st.warning(tr(language, "no_orders"))
        return
    total_missing = int(data.isna().sum().sum())
    duplicate_rows = int(data.duplicated().sum())
    kpi_row(
        [
            {"icon": "📋", "label": tr(language, "rows"), "value": indian_number(len(data)), "note": tr(language, "explore_subtitle")},
            {"icon": "🧩", "label": tr(language, "columns"), "value": indian_number(data.shape[1]), "note": tr(language, "profile")},
            {"icon": "🔍", "label": tr(language, "empty_cells"), "value": indian_number(total_missing), "note": tr(language, "empty_note")},
            {"icon": "🪞", "label": tr(language, "repeated"), "value": indian_number(duplicate_rows), "note": tr(language, "repeated_note")},
        ]
    )
    section_header(tr(language, "orders_heading"), tr(language, "filter_help"))
    st.dataframe(data, width="stretch", hide_index=True, height=480)
    st.download_button(
        tr(language, "download_csv"),
        data=data.to_csv(index=False).encode("utf-8"),
        file_name="business_data_filtered.csv",
        mime="text/csv",
        width="content",
    )

    section_header(tr(language, "profile"), tr(language, "profile_note"))
    profile = pd.DataFrame(
        {
            "Column": data.columns,
            "Type": [str(data[column].dtype) for column in data.columns],
            "Non-null": [int(data[column].notna().sum()) for column in data.columns],
            "Missing": [int(data[column].isna().sum()) for column in data.columns],
            "Distinct": [int(data[column].nunique(dropna=True)) for column in data.columns],
        }
    )
    st.dataframe(profile, width="stretch", hide_index=True)
    if {"Sales", "Profit"}.issubset(data.columns):
        st.write("")
        left, right = st.columns(2)
        with left:
            show_chart(charts.ship_mode_bar(data, language))
        with right:
            show_chart(charts.discount_profitability(data, language))


def predict_scenario(reg_model, clf_model, scaler, quantity: int, discount: float, year: int, month: int, quarter: int):
    values = [quantity, discount, year, month, quarter]
    feature_names = list(getattr(scaler, "feature_names_in_", ["Quantity", "Discount", "Year", "Month", "Quarter"]))
    scaled = scaler.transform(pd.DataFrame([values], columns=feature_names))
    sales_prediction = float(reg_model.predict(scaled)[0])
    profit_prediction = int(clf_model.predict(scaled)[0])
    confidence = None
    if hasattr(clf_model, "predict_proba") and 1 in clf_model.classes_:
        confidence = float(clf_model.predict_proba(scaled)[0][list(clf_model.classes_).index(1)])
    return sales_prediction, profit_prediction, confidence


def forecast_page(data: pd.DataFrame, language: str) -> None:
    hero(tr(language, "forecast_title"), tr(language, "forecast_subtitle"), tr(language, "forecast"))
    if data.empty:
        st.warning(tr(language, "no_orders"))
        return
    years = data["Order Date"].dropna().dt.year if "Order Date" in data else pd.Series(dtype=int)
    default_year = int(years.max()) if not years.empty else 2024
    dated_orders = data["Order Date"].dropna() if "Order Date" in data else pd.Series(dtype="datetime64[ns]")
    default_month = int(dated_orders.max().month) if not dated_orders.empty else 6
    months = month_names(language)
    with st.form("scenario_form"):
        section_header(tr(language, "order_idea"), tr(language, "order_idea_note"))
        col1, col2, col3 = st.columns(3)
        with col1:
            quantity = st.number_input(
                tr(language, "quantity"),
                min_value=1,
                max_value=100,
                value=5,
                step=1,
                help=tr(language, "quantity_help"),
            )
            discount_percent = st.number_input(
                tr(language, "discount"),
                min_value=0.0,
                max_value=100.0,
                value=10.0,
                step=1.0,
                format="%.0f",
                help=tr(language, "discount_help"),
            )
        with col2:
            year = st.number_input(
                tr(language, "year"),
                min_value=2000,
                max_value=2100,
                value=default_year,
                step=1,
                help=tr(language, "year_help"),
            )
            month = st.selectbox(
                tr(language, "month"),
                options=list(range(1, 13)),
                index=default_month - 1,
                format_func=lambda month_number: months[month_number - 1],
                key="forecast_month_number",
                help=tr(language, "month_help"),
            )
        with col3:
            quarter = (int(month) - 1) // 3 + 1
            st.text_input(tr(language, "quarter"), value=f"Q{quarter}", disabled=True, help=tr(language, "order_idea_note"))
            st.caption(tr(language, "estimate_note"))
        submitted = st.form_submit_button(tr(language, "run_forecast"), width="stretch")

    if submitted:
        try:
            models = load_models()
            discount = float(discount_percent) / 100
            result = predict_scenario(*models, int(quantity), discount, int(year), int(month), int(quarter))
            comparison_discount = max(0.0, discount - 0.1)
            comparison = predict_scenario(*models, int(quantity), comparison_discount, int(year), int(month), int(quarter))
            st.session_state["forecast_result"] = {
                "inputs": (int(quantity), discount, int(year), int(month), int(quarter)),
                "result": result,
                "comparison": comparison,
                "comparison_discount": comparison_discount,
            }
        except (FileNotFoundError, OSError, ValueError, TypeError) as exc:
            st.error(tr(language, "forecast_error", error=exc))

    result = st.session_state.get("forecast_result")
    if result is None:
        return
    sales_prediction, profit_prediction, confidence = result["result"]
    section_header(tr(language, "result"), f"{result['inputs'][0]} · {result['inputs'][1]:.0%} · {months[result['inputs'][3] - 1]} {result['inputs'][2]}")
    metrics = [
        {"icon": "💵", "label": tr(language, "possible_sales"), "value": currency(sales_prediction), "note": tr(language, "not_promise")},
        {"icon": "📊", "label": tr(language, "profit_likely"), "value": tr(language, "looks_likely") if profit_prediction == 1 else tr(language, "looks_unlikely"), "note": tr(language, "check_costs")},
    ]
    if confidence is not None:
        metrics.append({"icon": "🎯", "label": tr(language, "profit_chance"), "value": f"{confidence:.0%}", "note": tr(language, "rough_chance")})
    kpi_row(metrics)
    comparison_sales, comparison_profit, _ = result["comparison"]
    st.write("")
    st.markdown(tr(
        language,
        "lower_discount",
        discount=f"{result['comparison_discount']:.0%}",
        sales=currency(comparison_sales),
        outlook=tr(language, "more_likely") if comparison_profit == 1 else tr(language, "less_likely"),
    ))
    st.caption(tr(language, "comparison_note"))


def reports_page(data: pd.DataFrame, language: str) -> None:
    hero(tr(language, "report_title"), tr(language, "report_subtitle"), tr(language, "reports"))
    if data.empty:
        st.warning(tr(language, "no_orders"))
        return
    local_report = executive_summary(data, language)
    section_header(tr(language, "your_summary"), tr(language, "summary_note"))
    st.text(local_report)
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button(
            tr(language, "ai_ideas"),
            width="stretch",
            help=tr(language, "ai_missing"),
            disabled=not bool(CONFIG.groq_api_key),
        ):
            ai_language = LANGUAGES[language]
            context = (
                f"You are helping a small shop owner. Respond entirely in {ai_language}. Use short, plain language and avoid business jargon. "
                f"Based only on these numbers, give three simple things the owner could check or try. "
                f"Say clearly that suggestions are not guarantees. Do not invent facts.\n\n{local_report}"
            )
            with st.spinner(tr(language, "preparing_ai")):
                ai_result = ask_genai(context)
            st.session_state["ai_report"] = {
                "source": local_report,
                "language": language,
                "text": f"{local_report}\n\n{tr(language, 'ai_result')}\n{ai_result}",
            }
        if not CONFIG.groq_api_key:
            st.caption(tr(language, "ai_missing"))
    with col2:
        st.download_button(
            tr(language, "download_pdf"),
            data=pdf_bytes(local_report, tr(language, "your_summary")),
            file_name="shop_summary.pdf",
            mime="application/pdf",
            width="stretch",
        )
    saved_report = st.session_state.get("ai_report")
    if saved_report and saved_report["source"] == local_report and saved_report["language"] == language:
        section_header(tr(language, "ai_result"))
        st.text(saved_report["text"])
        st.download_button(
            tr(language, "download_pdf"),
            data=pdf_bytes(saved_report["text"], tr(language, "ai_result")),
            file_name="shop_summary_with_ideas.pdf",
            mime="application/pdf",
        )


authenticated_user = st.session_state.get("authenticated_user")
if authenticated_user:
    if not require_atlas():
        st.stop()
    try:
        authenticated_user = get_user(authenticated_user.get("id", ""))
    except PyMongoError:
        st.error("Could not verify your account with Atlas. Check the app logs.")
        st.stop()
    if authenticated_user is None:
        st.session_state.clear()
        st.warning("Your account could not be found. Please sign in again.")
        st.stop()
    st.session_state["authenticated_user"] = authenticated_user
else:
    authenticated_user = None
    if not st.session_state.get("guest_mode"):
        render_auth_page()
        st.stop()

try:
    page, filtered_data, selected_language, saved_metadata = render_sidebar(
        load_default_data(), authenticated_user
    )
except (FileNotFoundError, OSError, pd.errors.ParserError) as exc:
    st.error(tr("English", "sample_error", error=exc))
    st.stop()

if page == "overview":
    overview_page(filtered_data, selected_language)
elif page == "explore":
    explore_page(filtered_data, selected_language)
elif page == "forecast":
    forecast_page(filtered_data, selected_language)
elif page == "database" and authenticated_user is not None:
    database_page(authenticated_user, saved_metadata)
else:
    reports_page(filtered_data, selected_language)

st.markdown(f'<div class="footer">{tr(selected_language, "footer")}</div>', unsafe_allow_html=True)
