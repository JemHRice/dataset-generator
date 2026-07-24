# Generator assumptions

This dataset is synthetic. That is a liability unless the assumptions behind it
are written down, so this document states every non-trivial distribution the
generator uses and the reasoning behind it. If a figure in the analysis looks
surprising, check it against the assumption here first — the number is only as
real as the rule that produced it.

Everything below is driven by [`config.py`](../config.py); the values quoted are
the defaults. Where a rule lives in code rather than config, the function in
[`generate_db.py`](../generate_db.py) is named.

## Scope and grain

| Thing | Value |
|---|---|
| Period | 2020-01-01 → 2024-12-31 (5 years, 1,827 days) |
| Orders | ~400k target (actual varies with seasonality/jitter) |
| Line items | ~1.7M (avg ~3.4 per order) |
| Customers | 75,000 |
| Products | 400 across 9 sport categories |
| Stores | 50, distributed across 8 AU states by population weight |
| Region | Australia — AU financial year (Jul–Jun), AU seasons, AU public holidays |

## Demand model (`generate_fact_orders`)

Daily order volume is a base rate multiplied by independent factors:

```
daily_volume = base_rate
             × yearly_multiplier      # year-on-year growth
             × month_multiplier       # seasonality
             × holiday_multiplier     # public holidays
             × (1 + promo_boost)      # active promotions
             × jitter                 # ±15% noise
```

- **Year-on-year growth** — starts at 1.0 in the first year and each subsequent
  year steps by a random −5% to +15%, compounding. Derived from the configured
  date range, so it holds whatever `START_DATE`/`END_DATE` you set.
- **Seasonality** — monthly weights peak in December (1.4×, Christmas) and
  January (1.3×, New Year), trough in February (0.9×). Spring (Oct) is a
  secondary peak at 1.2×.
- **Public holidays** — trade drops to `PUBLIC_HOLIDAY_VOLUME_MULTIPLIER` (0.45)
  of a normal day. This is the only thing `dim_date.is_public_holiday` drives.
- **Promotions** — during a promo window, daily volume lifts by a random
  20–60% and the promoted category's products are 1.5× more likely to be
  chosen (deduplicated, so overlapping promos on one category don't compound).
- **Jitter** — a final ±15% uniform multiplier so no two days are identical.

## Customers (`generate_dim_customer`)

- **Acquisition** — `CUSTOMER_INITIAL_BASE_FRACTION` (0.40) of customers exist on
  day one; the rest are acquired across the range, skewed toward later dates
  (`u**0.8`) to model a growing business. An order can only ever be placed by a
  customer who had already signed up by that date.
- **Repeat purchasing** — each customer carries a hidden lognormal frequency
  weight (`CUSTOMER_REPEAT_SIGMA` = 1.0): a few buy a lot, most buy rarely. This
  is what makes RFM, cohort-retention, and CLV analysis meaningful rather than
  uniform.
- **Demographics** — gender 49/49/2 (M/F/Other); DOB 1955–2006; home state by
  population weight.
- **Known limitation** — there is no churn. A customer's frequency weight never
  decays, so retention curves are optimistic. Modelling churn is Phase 2.

## Products and pricing (`generate_dim_product`)

- **Cost by price band** — unit cost is drawn from a per-subcategory band
  (`PRICE_BANDS` × `SUBCATEGORY_PRICE_BAND`), not a blind random tier. A cricket
  ball lands in the accessory band ($3–25 cost), a bike in big-ticket
  ($200–1500). This keeps product-level price analysis meaningful.
- **Sale price** — `unit_cost × category margin` (1.35× Swimming to 1.6× Golf).
- **Known limitation** — price is static over the five years; there is no price
  history, so `unit_price_at_sale` never diverges from the catalogue price.
  SCD Type 2 on the product dimension is Phase 2.

## Orders and line items (`generate_fact_order_items`)

- **Basket size** — 1–5 items, weighted toward 3–4.
- **Discounts** — a promoted line takes its promotion's rate (±5% noise); a
  non-promoted line is undiscounted 70% of the time, otherwise 5–25%. Every
  discount is capped so the line keeps ~5% gross margin above cost — no line
  ever sells below cost.
- **Order value** — `SUM(line_total) + shipping_cost`. The header reconciles
  exactly to its lines plus shipping.
- **Order status** — 94% Delivered, 3% Processing, 3% Cancelled. Cancelled and
  Processing orders still carry line items (as in real systems), so summing
  `line_total` across the raw table over-counts revenue — use `vw_net_sales` or
  filter to Delivered for recognised revenue.

## Fulfillment (`generate_fact_orders`)

- **Method mix** — weighted, not uniform: Standard 50%, Express 22%,
  Click & Collect 15%, Overnight 8%, Same Day 5%.
- **Dates** — only Delivered orders get a ship date (0–2 day processing lag) and
  a delivery date (transit drawn from the method's min/max days). Click & Collect
  is in-store pickup: it gets a ready/ship date but never a delivery date.
  Delivery dates falling past the end of `dim_date` are left NULL (in transit).

## Reproducibility

`USE_FIXED_SEED = True` with `RANDOM_SEED = 42` gives a byte-stable dataset
across runs. Set it to `False` for a fresh random dataset each time.
