# Sports Retail Dataset Generator

Generates a realistic 5-year PostgreSQL sales database for an Australian sports retail business — ready to connect straight to Power BI.

Produces ~440k orders, ~1.5M line items, 50 stores, 400 products, 75k customers, and 10 promotional events across 9 sport categories. All randomised each run so every dataset is unique.

---

## What you need

- [PostgreSQL](https://www.postgresql.org/download/windows/) installed and running
- [Python 3.9+](https://www.python.org/downloads/) — tick "Add Python to PATH" during install
- [Git](https://git-scm.com/download/win)

---

## Setup

```powershell
git clone https://github.com/JemHRice/dataset-generator.git
cd dataset-generator

python -m venv venv
venv\Scripts\activate

pip install -r requirements.txt
```

Copy `.env.example` to `.env` and update the password to match your PostgreSQL install:

```
DB_PASSWORD=your_password_here
```

Then run:

```powershell
python generate_db.py
```

Takes about 3–5 minutes. Creates a database called `sports_retail` on `localhost:5432`.

---

## Customisation

**`config.py` is the only file you need to touch.** Everything is in there — data volumes, date range, states, store locations, sport categories, shipping methods, and promotional events. Each setting has a comment explaining what it does.

A few things worth knowing:
- If you rename a category in `CATEGORIES`, update any matching `PROMOTIONS` entries too — the category field links them
- `USE_FIXED_SEED = True` gives the same dataset every run, useful for sharing identical data
- Re-running the script drops and recreates the database from scratch

---

## Connecting to Power BI

You'll need the PostgreSQL connector — download `Npgsql-4.0.10.msi` from the [Npgsql v4.0.10 release page](https://github.com/npgsql/npgsql/releases/tag/v4.0.10) and restart Power BI after installing.

Then: **Get Data → PostgreSQL** → server `localhost`, database `sports_retail`. Use **Import** mode.

---

## Schema

8 dimension tables + 2 fact tables (+ 1 view):

| Table | Description |
|---|---|
| `dim_state` | States with population weights |
| `dim_store` | Store locations by state |
| `dim_salesperson` | Staff assigned to stores |
| `dim_product` | Products across all categories |
| `dim_customer` | Customers with demographics, home state, and signup date |
| `dim_shipping_method` | Delivery options and costs |
| `dim_promotions` | Sales events with discount rates |
| `dim_date` | Daily records with season, financial year, public holidays |
| `fact_orders` | Order headers, incl. ship/delivery dates |
| `fact_order_items` | Line items with quantity, price, discount, and promotion |
| `vw_net_sales` | View: delivered line items only (recognised revenue) |

**Customers and repeat buying.** Customers aren't assigned to orders uniformly — each has a hidden purchase-frequency weight (a few buy a lot, most buy rarely), and orders only ever go to customers who had already signed up by the order date. This makes repeat-rate, RFM, cohort-retention, new-vs-returning, and CLV-over-time analysis meaningful. Tune the base size and skew via `CUSTOMER_INITIAL_BASE_FRACTION` and `CUSTOMER_REPEAT_SIGMA` in `config.py`.

**Fulfillment timing.** `fact_orders` carries `order_date_id`, `ship_date_id`, and `delivery_date_id` (the latter two are role-playing date relationships — use `USERELATIONSHIP` in DAX). Only `Delivered` orders have ship/delivery dates; `Processing` and `Cancelled` have none.

**Revenue vs. operational analysis.** `Cancelled` and `Processing` orders still carry line items (as they do in real life), so summing `line_total` across the raw table over-counts revenue. For revenue measures, build on `vw_net_sales` (delivered only) or filter `order_status = 'Delivered'`. Use the raw fact tables for funnel/cancellation/operational analysis where every status matters.

**Relationships for Power BI:**

| From | To | Key |
|---|---|---|
| `fact_orders` | `dim_date` | `order_date_id → date_id` (active) |
| `fact_orders` | `dim_date` | `ship_date_id → date_id` (inactive / role-playing) |
| `fact_orders` | `dim_date` | `delivery_date_id → date_id` (inactive / role-playing) |
| `fact_orders` | `dim_store` | `store_id` |
| `fact_orders` | `dim_salesperson` | `salesperson_id` |
| `fact_orders` | `dim_customer` | `customer_id` |
| `fact_orders` | `dim_shipping_method` | `shipping_method_id` |
| `fact_order_items` | `fact_orders` | `order_id` |
| `fact_order_items` | `dim_product` | `product_id` |
| `fact_order_items` | `dim_promotions` | `promotion_id` |
| `dim_customer` | `dim_state` | `state_id` |
| `dim_store` | `dim_state` | `state_id` |
