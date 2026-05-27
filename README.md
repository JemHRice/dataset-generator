# Sports Retail Database Generator

A tool that generates a realistic 5-year sales database for an Australian sports retail business, ready to connect to Power BI.

---

## What this does

Running the script creates a PostgreSQL database called `sports_retail` populated with:

- ~440,000 customer orders across 5 years (2020–2024)
- ~1.5 million line items
- 50 stores distributed across Australian states
- 400 products across 9 sport categories
- 10 promotional events with category discounts
- Realistic seasonality, yearly trends, and geographic variation

All of this can be customised in `config.py` before you run the script.

---

## Prerequisites

Before you start, you need three things installed on your computer:

1. **PostgreSQL** — the database server  
   → Download from: postgresql.org/download/windows  
   → During installation, set a password for the `postgres` user and remember it

2. **Python 3.9 or newer**  
   → Download from: python.org/downloads  
   → During installation, tick **"Add Python to PATH"**

3. **Git**  
   → Download from: git-scm.com/download/win

---

## Setup (step by step)

### 1. Get the project

Open **PowerShell** (search for it in the Start menu) and run:

```powershell
git clone <repo_url>
cd sports-store-analysis
```

### 2. Create a virtual environment

This keeps the project's dependencies separate from the rest of your system:

```powershell
python -m venv venv
venv\Scripts\activate
```

Your prompt should now show `(venv)` at the start.

### 3. Install dependencies

```powershell
pip install -r requirements.txt
```

### 4. Set your database password

Open the `.env` file in a text editor and update the password to match what you set when installing PostgreSQL:

```
DB_HOST=localhost
DB_PORT=5432
DB_NAME=sports_retail
DB_USER=postgres
DB_PASSWORD=your_password_here
```

### 5. Customise your data (optional)

Open `config.py` in a text editor. This is the **only file you need to edit** to change anything about the data. See the [Customisation](#customisation) section below for what you can change.

### 6. Run the generator

```powershell
python generate_db.py
```

The script will print its progress and tell you when it's done. Expect it to take 3–5 minutes depending on your settings.

---

## Customisation

Everything you can change lives in `config.py`. Open it in any text editor — every setting has a comment explaining what it does.

### What you can change

| Section | What it controls |
|---|---|
| `USE_FIXED_SEED` | Whether everyone gets the same data or unique data each run |
| `TARGET_ORDERS` | How many orders to generate |
| `NUM_STORES` / `NUM_PRODUCTS` etc. | How many of each dimension to create |
| `START_DATE` / `END_DATE` | The time period the data covers |
| `STATES` | Which states/regions exist and their relative activity levels |
| `SUBURBS_BY_STATE` | Which cities/suburbs stores can be located in |
| `CATEGORIES` | Which sports to sell, their subcategories, product counts, and margins |
| `SHIPPING_METHODS` | Delivery options, carriers, costs, and timeframes |
| `PROMOTIONS` | Sales events — names, dates, discount rates, and which category they apply to |
| `PUBLIC_HOLIDAYS` | Holidays used to adjust order volumes |

### Example: adding a new sport

In `config.py`, add a new entry to `CATEGORIES`:

```python
"Rugby League": {
    "subcategories": ["Balls", "Jerseys", "Boots", "Protective Gear"],
    "products": 35,
    "margin": 1.4,
},
```

Then add a promotion for it if you want:

```python
{
    "name": "NRL Grand Final Sale",
    "start_date": (2023, 10, 1),
    "end_date":   (2023, 10, 7),
    "discount_rate": 0.20,
    "category": "Rugby League",
},
```

### Example: changing to a different country

Update `STATES` with your regions, `SUBURBS_BY_STATE` with your cities, and `PUBLIC_HOLIDAYS` with your country's holidays.

### Generating unique data each time

By default `USE_FIXED_SEED = False`, which means every run produces a different random dataset. If you want the exact same data every time (useful for sharing or reproducibility), set:

```python
USE_FIXED_SEED = True
```

---

## Connecting to Power BI

### Step 1 — Install the PostgreSQL connector

Power BI needs an extra driver to connect to PostgreSQL. Download and install **Npgsql v4.0.10**:

- Go to: github.com/npgsql/npgsql/releases/tag/v4.0.10
- Download `Npgsql-4.0.10.msi` and run the installer
- Restart Power BI after installing

### Step 2 — Connect

1. Open **Power BI Desktop**
2. Click **Get Data** → search for **PostgreSQL** → select it → click **Connect**
3. Enter:
   - **Server:** `localhost`
   - **Database:** `sports_retail`
4. When prompted for credentials: select **Database**, enter username `postgres` and your password
5. Select all 9 tables and click **Load**

### Step 3 — Use Import mode

When asked, choose **Import** (not DirectQuery). The data is static so Import gives much faster visuals.

---

## Database schema

### Dimension tables

| Table | Rows | Description |
|---|---|---|
| `dim_state` | 8 | Australian states with population weights |
| `dim_store` | ~50 | Store locations distributed by state |
| `dim_salesperson` | ~100 | Sales staff assigned to stores |
| `dim_product` | 400 | Products across all sport categories |
| `dim_shipping_method` | 5 | Delivery options and costs |
| `dim_promotions` | 10 | Promotional events with discount rates |
| `dim_date` | 1,827 | Daily records with season, financial year, holidays |

### Fact tables

| Table | Rows | Description |
|---|---|---|
| `fact_orders` | ~440,000 | Order headers with store, salesperson, date, status |
| `fact_order_items` | ~1.5M | Line items with product, quantity, price, discount |

### Connecting tables in Power BI

| From | To | Join column |
|---|---|---|
| `fact_orders` | `dim_date` | `order_date_id` → `date_id` |
| `fact_orders` | `dim_store` | `store_id` → `store_id` |
| `fact_orders` | `dim_salesperson` | `salesperson_id` → `salesperson_id` |
| `fact_orders` | `dim_shipping_method` | `shipping_method_id` → `shipping_method_id` |
| `fact_order_items` | `fact_orders` | `order_id` → `order_id` |
| `fact_order_items` | `dim_product` | `product_id` → `product_id` |
| `dim_store` | `dim_state` | `state_id` → `state_id` |

---

## Troubleshooting

### "Database connection failed"

- Make sure PostgreSQL is running (check Services in Windows)
- Check the password in your `.env` file matches what you set during PostgreSQL installation
- Try connecting with pgAdmin first to confirm your credentials work

### "Module not found" or import errors

Make sure your virtual environment is activated — your prompt should show `(venv)`:

```powershell
venv\Scripts\activate
pip install -r requirements.txt
```

### Generation is slow or seems stuck

- This is normal — 400,000 orders takes 3–5 minutes
- Don't close the window; let it finish
- If you want faster generation, reduce `TARGET_ORDERS` in `config.py`

### Power BI can't connect to PostgreSQL

- Make sure you installed Npgsql v4.0.10 (not a newer version)
- Restart Power BI after installing Npgsql
- Confirm PostgreSQL is running

### Re-running the script

Running the script again will drop and recreate the database from scratch, giving you a fresh dataset. This is intentional.
