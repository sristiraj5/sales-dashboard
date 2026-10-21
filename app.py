"""SalesPulse | Retail sales analytics portfolio dashboard.

Launch with: streamlit run app.py
Stack: Python, Streamlit, SQLite, pandas, Plotly.
"""

from datetime import date
from math import ceil

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.analytics import (
    SalesFilters, count_orders, get_breakdown, get_kpis,
    get_monthly_trend, get_orders, get_top_products,
)
from src.catalog import CHANNELS, PAYMENT_METHODS, REGIONS, STATUSES
from src.db import add_order, get_date_bounds, get_products, initialize_database

st.set_page_config(
    page_title="SalesPulse | Retail Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

NAVY = "#1E2A4B"
PURPLE = "#6658E9"
TEAL = "#11A9A1"
ORANGE = "#F39B52"
MUTED = "#7A839D"
PALETTE = [PURPLE, TEAL, ORANGE, "#3E80D7", "#9A6DF0"]

CSS = """
<style>
  @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&display=swap');
  html, body, [class*="css"], [data-testid="stAppViewContainer"] { font-family: 'DM Sans', sans-serif; }
  [data-testid="stAppViewContainer"] { background: #F5F7FB; }
  .block-container { max-width: 1460px; padding-top: 1.7rem; padding-bottom: 3.5rem; }
  [data-testid="stSidebar"] { background: #FFFFFF; border-right: 1px solid #E9EDF6; }
  [data-testid="stSidebar"] .block-container { padding-top: 1.3rem; }
  [data-testid="stSidebar"] [data-testid="stRadio"] label { font-weight: 600; }
  #MainMenu, footer, [data-testid="stDecoration"] { visibility: hidden; }
  .brand { font-size: 1.7rem; font-weight: 800; letter-spacing: -1.2px; color: #1D2948; margin-bottom: .1rem; }
  .brand-mark { display: inline-grid; place-items: center; background: #6658E9; color: white;
      border-radius: 12px; width: 39px; height: 39px; font-size: 1.3rem; margin-right: 8px; }
  .brand-sub { font-size: .78rem; color: #8B92A8; padding-left: 49px; margin-bottom: 1.35rem; }
  .eyebrow { font-weight: 800; color: #6658E9; letter-spacing: 1.7px; text-transform: uppercase; font-size: .69rem; margin-bottom: .5rem; }
  .page-title { font-size: clamp(1.9rem, 3vw, 2.65rem); font-weight: 800; color: #1D2948;
     letter-spacing: -1.5px; line-height: 1.2; margin: .2rem 0 .45rem; }
  .page-sub { color: #7C869E; font-size: .91rem; margin-bottom: 1.25rem; }
  .demo-pill { display: inline-block; font-size: .68rem; background: #E8F8F5; color: #10887F;
      padding: .35rem .7rem; border-radius: 100px; font-weight: 800; letter-spacing: .7px; }
  .metric { min-height: 138px; background: white; border: 1px solid #E9ECF3;
      border-radius: 18px; padding: 18px 20px; box-shadow: 0 4px 15px rgba(25,35,65,.025); margin-bottom: 10px; }
  .metric-row { display: flex; align-items: center; justify-content: space-between; }
  .metric-label { color: #828BA1; font-weight: 700; font-size: .80rem; }
  .metric-icon { font-size: 1rem; background: #F0EEFF; border-radius: 10px; padding: 8px 11px; }
  .metric-value { color: #1F2B4A; font-size: clamp(1.35rem, 2vw, 2.0rem); font-weight: 800;
     letter-spacing: -1px; line-height: 1.5; }
  .metric-foot { font-size: .74rem; color: #9199AD; }
  .section-title { color: #1F2B4A; font-size: 1.15rem; letter-spacing: -.3px; font-weight: 800;
      margin-top: .7rem; margin-bottom: .2rem; }
  .section-caption { color: #929AAE; font-size: .78rem; margin-bottom: .65rem; }
  .insight { padding: 16px 18px; background: #F0EEFF; border-left: 4px solid #6658E9;
      border-radius: 13px; margin: 4px 0 12px; font-size: .86rem; color: #333C65; }
  .fineprint { font-size: .76rem; color: #8C94A7; margin: 1.2rem 0; }
  div[data-testid="stVerticalBlockBorderWrapper"] > div { border-color: #EBEDF4; }
  .stDownloadButton button, .stFormSubmitButton button { border-radius: 12px !important; font-weight: 700; }
  div[data-testid="stMetric"] { background: white; }
</style>
"""


def money(amount: float, compact: bool = True) -> str:
    """Format dashboard amounts as rupees; numbers are demonstrative."""
    amount = float(amount or 0)
    sign = "−" if amount < 0 else ""
    amount = abs(amount)
    if compact and amount >= 10_000_000:
        return f"{sign}₹{amount / 10_000_000:,.2f}Cr"
    if compact and amount >= 100_000:
        return f"{sign}₹{amount / 100_000:,.2f}L"
    return f"{sign}₹{amount:,.0f}"


def metric_card(label: str, value: str, foot: str, icon: str) -> None:
    st.markdown(f"""
      <div class="metric">
        <div class="metric-row"><span class="metric-label">{label}</span><span class="metric-icon">{icon}</span></div>
        <div class="metric-value">{value}</div>
        <div class="metric-foot">{foot}</div>
      </div>
    """, unsafe_allow_html=True)


def title(text: str, caption: str = "") -> None:
    st.markdown(f'<div class="section-title">{text}</div><div class="section-caption">{caption}</div>', unsafe_allow_html=True)


def layout_chart(fig: go.Figure, height: int = 320, showlegend: bool = False) -> go.Figure:
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="DM Sans, sans-serif", color=NAVY, size=12),
        margin=dict(l=15, r=18, t=20, b=20), height=height,
        showlegend=showlegend,
        legend=dict(orientation="h", y=1.08, x=0, font=dict(size=11)),
        hoverlabel=dict(bgcolor="#FFFFFF", font_color=NAVY),
    )
    fig.update_xaxes(showgrid=False, zeroline=False, linecolor="#E7ECF5", tickfont=dict(color=MUTED, size=11))
    fig.update_yaxes(showgrid=True, gridcolor="#EDF0F6", zeroline=False, tickfont=dict(color=MUTED, size=11))
    return fig


def show_chart(fig: go.Figure) -> None:
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def page_header(eyebrow: str, heading: str, subtitle: str) -> None:
    st.markdown(f"""
      <div class="eyebrow">{eyebrow}</div>
      <div class="page-title">{heading}</div>
      <div class="page-sub">{subtitle} &nbsp; <span class="demo-pill">● SYNTHETIC DEMO DATA</span></div>
    """, unsafe_allow_html=True)


def display_overview(filters: SalesFilters) -> None:
    page_header("BUSINESS OVERVIEW", "Sales performance, at a glance.", "Understand growth, profitability and where revenue comes from.")
    metrics = get_kpis(filters)
    cards = [
        ("Net revenue", money(metrics["total_revenue"]), "Delivered orders · after discount", "💳"),
        ("Gross profit", money(metrics["gross_profit"]), "Revenue minus product costs", "📈"),
        ("Fulfilled orders", f"{metrics['delivered_orders']:,.0f}", "Successfully delivered", "📦"),
        ("Average order value", money(metrics["aov"], False), "Revenue ÷ delivered orders", "🛍️"),
        ("Gross margin", f"{metrics['margin_pct']:.1f}%", "Profit as a share of revenue", "🎯"),
        ("Return rate", f"{metrics['return_pct']:.1f}%", "Returned ÷ all orders", "↩️"),
    ]
    for row_start in (0, 3):
        cols = st.columns(3, gap="medium")
        for col, args in zip(cols, cards[row_start:row_start + 3]):
            with col:
                metric_card(*args)
    if not metrics["all_orders"]:
        st.info("No orders match these filters. Select a wider date range or clear some filters.")
        return

    monthly = get_monthly_trend(filters)
    regions = get_breakdown(filters, "region")
    categories = get_breakdown(filters, "category")
    channels = get_breakdown(filters, "channel")
    status = get_breakdown(filters, "status")
    products = get_top_products(filters)

    st.write("")
    left, right = st.columns([1.62, 1], gap="large")
    with left:
        with st.container(border=True):
            title("Revenue & gross profit", "Monthly performance · INR")
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=monthly["month"], y=monthly["revenue"], mode="lines+markers", name="Revenue",
                line=dict(color=PURPLE, width=3), marker=dict(size=5),
                fill="tozeroy", fillcolor="rgba(102,88,233,.09)",
                hovertemplate="%{x}<br>Revenue: ₹%{y:,.0f}<extra></extra>",
            ))
            fig.add_trace(go.Scatter(
                x=monthly["month"], y=monthly["profit"], mode="lines+markers", name="Profit",
                line=dict(color=TEAL, width=3), marker=dict(size=5),
                hovertemplate="%{x}<br>Profit: ₹%{y:,.0f}<extra></extra>",
            ))
            fig.update_yaxes(tickprefix="₹", tickformat="~s")
            show_chart(layout_chart(fig, 326, True))
    with right:
        with st.container(border=True):
            title("Revenue by category", "Distribution of delivered sales")
            active = categories[categories["revenue"] > 0]
            if active.empty:
                st.info("No delivered sales in this selection.")
            else:
                fig = go.Figure(go.Pie(
                    labels=active["segment"], values=active["revenue"], hole=.65,
                    marker=dict(colors=PALETTE, line=dict(color="#FFFFFF", width=3)),
                    textinfo="percent", textposition="outside",
                    hovertemplate="%{label}<br>₹%{value:,.0f}<br>%{percent}<extra></extra>",
                ))
                fig.update_layout(annotations=[dict(text="CATEGORY<br>MIX", x=.5, y=.5,
                    font=dict(size=13, color=MUTED), showarrow=False)])
                show_chart(layout_chart(fig, 326, True))

    a, b = st.columns(2, gap="large")
    with a:
        with st.container(border=True):
            title("Top regions", "Net revenue by geographic region")
            subset = regions.sort_values("revenue", ascending=True)
            fig = go.Figure(go.Bar(
                x=subset["revenue"], y=subset["segment"], orientation="h",
                marker=dict(color=PURPLE, cornerradius=5),
                hovertemplate="%{y}: ₹%{x:,.0f}<extra></extra>",
            ))
            fig.update_xaxes(tickprefix="₹", tickformat="~s")
            show_chart(layout_chart(fig, 310))
    with b:
        with st.container(border=True):
            title("Sales channels", "How customers buy")
            fig = go.Figure(go.Bar(
                x=channels["segment"], y=channels["revenue"],
                marker=dict(color=[TEAL, PURPLE, "#72A8EF", ORANGE][:len(channels)], cornerradius=5),
                hovertemplate="%{x}: ₹%{y:,.0f}<extra></extra>",
            ))
            fig.update_yaxes(tickprefix="₹", tickformat="~s")
            show_chart(layout_chart(fig, 310))

    a, b = st.columns([1.4, 1], gap="large")
    with a:
        with st.container(border=True):
            title("Best-selling products", "Ranked by net revenue")
            best = products.head(7)[["product_name", "category", "revenue", "margin_pct"]].copy()
            st.dataframe(best, use_container_width=True, hide_index=True, height=295,
                column_config={
                    "product_name": "Product", "category": "Category",
                    "revenue": st.column_config.NumberColumn("Revenue (₹)", format="₹ %.0f"),
                    "margin_pct": st.column_config.NumberColumn("Margin", format="%.1f%%"),
                })
    with b:
        with st.container(border=True):
            title("Order fulfillment", "Statuses include all recorded orders")
            status_colors = {"Delivered": TEAL, "Returned": ORANGE, "Cancelled": "#E16C85"}
            fig = go.Figure(go.Pie(
                labels=status["segment"], values=status["orders"], hole=.66,
                marker=dict(colors=[status_colors.get(s, PURPLE) for s in status["segment"]]),
                textinfo="percent", textposition="outside",
                hovertemplate="%{label}: %{value:,} orders<extra></extra>",
            ))
            fig.update_layout(annotations=[dict(text=f"{int(metrics['all_orders']):,}<br>orders",
                x=.5, y=.5, showarrow=False, font=dict(size=15, color=NAVY))])
            show_chart(layout_chart(fig, 295, True))

    leading_region = regions.iloc[0]["segment"] if not regions.empty else "N/A"
    leading_category = categories.iloc[0]["segment"] if not categories.empty else "N/A"
    st.markdown(f'<div class="insight"><b>💡 Business takeaway:</b> <b>{leading_region}</b> generated the most revenue in this selection, while <b>{leading_category}</b> was the highest-earning product category. Use Product Insights to investigate further.</div>', unsafe_allow_html=True)


def display_products(filters: SalesFilters) -> None:
    page_header("PRODUCT INTELLIGENCE", "What is driving your sales?", "Explore category economics, product leaders and profit margins.")
    products = get_top_products(filters)
    categories = get_breakdown(filters, "category")
    if products.empty or products["revenue"].sum() <= 0:
        st.info("No fulfilled orders match these filters.")
        return
    c1, c2, c3 = st.columns(3)
    with c1:
        metric_card("Active products", str(int((products["units"] > 0).sum())), "Products with fulfilled sales", "🏷️")
    with c2:
        best = products.iloc[0]
        metric_card("Top product", best["product_name"], "By revenue in the selected period", "🥇")
    with c3:
        profitable = products[products["revenue"] > 0]
        weighted_margin = 100 * profitable["profit"].sum() / profitable["revenue"].sum()
        metric_card("Overall product margin", f"{weighted_margin:.1f}%", "Revenue-weighted gross margin", "📊")

    st.write("")
    left, right = st.columns([1.2, 1], gap="large")
    with left:
        with st.container(border=True):
            title("Top 10 products", "Revenue leaders · INR")
            top = products.head(10).sort_values("revenue")
            fig = go.Figure(go.Bar(
                x=top["revenue"], y=top["product_name"], orientation="h",
                marker=dict(color=PURPLE, cornerradius=5),
                hovertemplate="%{y}: ₹%{x:,.0f}<extra></extra>",
            ))
            fig.update_layout(margin=dict(l=10, r=14, t=14, b=8))
            fig.update_xaxes(tickprefix="₹", tickformat="~s")
            show_chart(layout_chart(fig, 410))
    with right:
        with st.container(border=True):
            title("Category revenue vs profit", "Profitability differs by category")
            fig = go.Figure()
            for name, color in (("revenue", PURPLE), ("profit", TEAL)):
                fig.add_trace(go.Bar(
                    x=categories["segment"], y=categories[name], name=name.title(),
                    marker=dict(color=color, cornerradius=4),
                    hovertemplate=f"%{{x}}<br>{name.title()}: ₹%{{y:,.0f}}<extra></extra>",
                ))
            fig.update_layout(barmode="group")
            fig.update_yaxes(tickprefix="₹", tickformat="~s")
            show_chart(layout_chart(fig, 410, True))

    with st.container(border=True):
        title("Revenue vs. margin", "Each bubble is a product · bubble size indicates units sold")
        visible = products[products["revenue"] > 0].copy()
        fig = px.scatter(
            visible, x="revenue", y="margin_pct", size="units", color="category",
            hover_name="product_name", hover_data={"revenue": ":,.0f", "margin_pct": ":.1f", "units": True},
            color_discrete_sequence=PALETTE, size_max=34,
            labels={"revenue": "Revenue (₹)", "margin_pct": "Gross margin (%)", "category": "Category"},
        )
        fig.update_traces(marker=dict(opacity=.78, line=dict(width=1.5, color="#FFFFFF")))
        fig.update_xaxes(tickprefix="₹", tickformat="~s")
        show_chart(layout_chart(fig, 370, True))

    with st.container(border=True):
        title("Complete product scorecard", "Sort by revenue, profit, margin or units in the table")
        st.dataframe(products, hide_index=True, use_container_width=True, height=380,
            column_config={
                "sku": "SKU", "product_name": "Product", "category": "Category",
                "revenue": st.column_config.NumberColumn("Revenue (₹)", format="₹ %.0f"),
                "profit": st.column_config.NumberColumn("Profit (₹)", format="₹ %.0f"),
                "margin_pct": st.column_config.NumberColumn("Margin", format="%.1f%%"),
            })
        st.download_button("⬇️ Download product scorecard", products.to_csv(index=False).encode("utf-8"),
            "salespulse_products.csv", "text/csv", key="product_csv")


def display_orders(filters: SalesFilters) -> None:
    page_header("ORDER EXPLORER", "Every order, fully searchable.", "Review individual transactions, investigate anomalies and export a CSV.")
    search = st.text_input("Search order ID, customer ID or product", placeholder="For example: ORD-000140 or Smartwatch")
    total = count_orders(filters, search)
    left, center, right = st.columns(3)
    with left:
        metric_card("Matching orders", f"{total:,}", "Includes delivered, returned and cancelled", "🧾")
    with center:
        kpi = get_kpis(filters)
        metric_card("Orders in date range", f"{kpi['all_orders']:,.0f}", "Before applying search", "🗓️")
    with right:
        metric_card("Rows per page", "25", "Navigate the paginated table below", "🔍")

    pages = max(1, ceil(total / 25))
    page = st.number_input("Page", min_value=1, max_value=pages, value=1, step=1, key=f"page_{search}_{total}")
    orders = get_orders(filters, search=search, limit=25, offset=(page - 1) * 25)
    orders = orders.assign(discount_pct=orders["discount"] * 100).drop(columns=["discount"])
    with st.container(border=True):
        title(f"Transactions · page {page} of {pages}", "Values are shown in INR; sales for returned/cancelled orders are ₹0")
        st.dataframe(orders, use_container_width=True, hide_index=True, height=640,
            column_config={
                "order_id": "Order ID", "order_date": "Date", "customer_id": "Customer",
                "product_name": "Product", "category": "Category", "quantity": "Qty",
                "unit_price": st.column_config.NumberColumn("Unit price", format="₹ %.0f"),
                "discount_pct": st.column_config.NumberColumn("Discount", format="%.0f%%"),
                "revenue": st.column_config.NumberColumn("Revenue", format="₹ %.0f"),
                "profit": st.column_config.NumberColumn("Profit", format="₹ %.0f"),
                "region": "Region", "channel": "Channel", "payment_method": "Payment", "status": "Status",
            })
    if total:
        # Export all matches, not just the 25 currently visible rows.
        all_matches = get_orders(filters, search=search, limit=None)
        st.download_button("⬇️ Export all matching orders (CSV)",
            data=all_matches.to_csv(index=False).encode("utf-8-sig"),
            file_name="salespulse_filtered_orders.csv", mime="text/csv", key="export_orders")
    else:
        st.info("No matching orders. Try another keyword or broaden the filters.")


def display_add_order() -> None:
    page_header("SQL DATA ENTRY", "Create a new sales order.", "Use the form to insert a record into SQLite and see it in the charts.")
    products = get_products()
    names = {f"{row.product_name}  ·  {row.sku}": row for row in products.itertuples(index=False)}
    with st.container(border=True):
        title("New transaction", "Catalog prices are pulled from the database and saved with each order")
        with st.form("add_order_form", clear_on_submit=False):
            a, b = st.columns(2, gap="large")
            with a:
                order_date = st.date_input("Order date", value=date.today())
                customer_id = st.text_input("Customer ID", placeholder="e.g. CUS-1001", max_chars=40)
                product_key = st.selectbox("Product", list(names.keys()))
                quantity = st.number_input("Quantity", min_value=1, max_value=100, value=1)
                discount_pct = st.slider("Discount (%)", 0, 90, 5)
            with b:
                region = st.selectbox("Region", REGIONS)
                channel = st.selectbox("Sales channel", CHANNELS)
                payment_method = st.selectbox("Payment method", PAYMENT_METHODS)
                status = st.selectbox("Order status", STATUSES)
                row = names[product_key]
                st.info(f"**Catalog:** ₹{row.list_price:,.0f} selling price · ₹{row.unit_cost:,.0f} unit cost")
            submitted = st.form_submit_button("➕ Save order to SQLite", type="primary", use_container_width=True)
        if submitted:
            try:
                order_id = add_order(
                    order_date=order_date, customer_id=customer_id, sku=names[product_key].sku,
                    quantity=int(quantity), discount_pct=discount_pct, region=region,
                    channel=channel, payment_method=payment_method, status=status,
                )
            except ValueError as exc:
                st.error(str(exc))
            else:
                st.success(f"Order {order_id} saved successfully. Open Overview or Order Explorer to see it.")

    st.markdown("""<div class="insight"><b>🧠 How the SQL works:</b> The form looks up price/cost with <code>SELECT</code>, validates inputs, and writes a new row with a parameterized <code>INSERT</code>. Dashboard metrics are calculated with <code>JOIN</code>, <code>CASE WHEN</code> and <code>GROUP BY</code>.</div>""", unsafe_allow_html=True)


def main() -> None:
    st.markdown(CSS, unsafe_allow_html=True)
    initialize_database()
    products = get_products()
    first_date, last_date = get_date_bounds()

    with st.sidebar:
        st.markdown('<div class="brand"><span class="brand-mark">↗</span>SalesPulse</div><div class="brand-sub">RETAIL ANALYTICS STUDIO</div>', unsafe_allow_html=True)
        page = st.radio("WORKSPACE", ["📊 Overview", "🏷️ Product Insights", "🧾 Order Explorer", "➕ Add Order"], label_visibility="collapsed")
        st.divider()
        st.markdown("**FILTER YOUR DATA**")
        period = st.date_input(
            "Order date range", value=(first_date, max(last_date, date.today())), min_value=first_date,
            max_value=max(date.today(), last_date), format="DD/MM/YYYY",
        )
        if isinstance(period, (tuple, list)) and len(period) == 2:
            start_date, end_date = period
        else:
            # Date-range picker can temporarily return one date while selecting.
            start_date, end_date = first_date, last_date
        regions = tuple(st.multiselect("Region", REGIONS, placeholder="All regions"))
        categories = tuple(st.multiselect("Product category", sorted(products["category"].unique()), placeholder="All categories"))
        channels = tuple(st.multiselect("Sales channel", CHANNELS, placeholder="All channels"))
        st.caption("Leave a filter empty to include all values. Filters apply to Overview, Product Insights and Order Explorer.")
        st.divider()
        st.markdown('<span class="demo-pill">● PORTFOLIO / DEMO</span>', unsafe_allow_html=True)
        st.markdown('<div class="fineprint">Python · SQL / SQLite · Streamlit · pandas · Plotly<br><br>Built with realistic-looking but entirely synthetic retail data. Not real company sales.</div>', unsafe_allow_html=True)

    filters = SalesFilters(start_date, end_date, regions, categories, channels)
    if page == "📊 Overview":
        display_overview(filters)
    elif page == "🏷️ Product Insights":
        display_products(filters)
    elif page == "🧾 Order Explorer":
        display_orders(filters)
    else:
        display_add_order()


if __name__ == "__main__":
    main()
