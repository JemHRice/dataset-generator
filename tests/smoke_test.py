"""Post-generation smoke test.

Connects to the database the generator just built and asserts the invariants
the generator is supposed to guarantee. Intended to run in CI straight after
`python generate_db.py` against a small dataset, but it works against any
generated database. Exits non-zero on the first failed check.

Reads the same DB_* environment variables as generate_db.py.
"""

import os
import sys

import psycopg2
from dotenv import load_dotenv

load_dotenv()

CONN = dict(
    host=os.getenv("DB_HOST", "localhost"),
    port=os.getenv("DB_PORT", "5432"),
    dbname=os.getenv("DB_NAME", "sports_retail"),
    user=os.getenv("DB_USER", "postgres"),
    password=os.getenv("DB_PASSWORD", ""),
)

# Each check returns (label, count_that_should_be_zero) unless noted.
CHECKS = [
    (
        "every table has rows",
        # Emits one row per empty table; expected empty.
        """
        SELECT t FROM (
            SELECT 'dim_state' t, COUNT(*) c FROM dim_state
            UNION ALL SELECT 'dim_store', COUNT(*) FROM dim_store
            UNION ALL SELECT 'dim_salesperson', COUNT(*) FROM dim_salesperson
            UNION ALL SELECT 'dim_product', COUNT(*) FROM dim_product
            UNION ALL SELECT 'dim_customer', COUNT(*) FROM dim_customer
            UNION ALL SELECT 'dim_shipping_method', COUNT(*) FROM dim_shipping_method
            UNION ALL SELECT 'dim_promotions', COUNT(*) FROM dim_promotions
            UNION ALL SELECT 'dim_date', COUNT(*) FROM dim_date
            UNION ALL SELECT 'fact_orders', COUNT(*) FROM fact_orders
            UNION ALL SELECT 'fact_order_items', COUNT(*) FROM fact_order_items
        ) x WHERE c = 0
        """,
    ),
    (
        "order header reconciles to lines + shipping",
        """
        SELECT o.order_id
        FROM fact_orders o
        JOIN (
            SELECT order_id, SUM(line_total) s
            FROM fact_order_items GROUP BY order_id
        ) li ON li.order_id = o.order_id
        WHERE ABS(o.total_order_value - (li.s + o.shipping_cost)) > 0.01
        """,
    ),
    (
        "no line sold below unit cost",
        """
        SELECT oi.order_item_id
        FROM fact_order_items oi
        JOIN dim_product p ON p.product_id = oi.product_id
        WHERE oi.unit_price_at_sale * (1 - oi.discount_applied) < p.unit_cost
        """,
    ),
    (
        "in-store pickup has no delivery date",
        """
        SELECT o.order_id
        FROM fact_orders o
        JOIN dim_shipping_method sm ON sm.shipping_method_id = o.shipping_method_id
        WHERE sm.carrier = 'In-Store' AND o.delivery_date_id IS NOT NULL
        """,
    ),
    (
        "delivery never precedes ship, ship never precedes order",
        """
        SELECT o.order_id
        FROM fact_orders o
        JOIN dim_date od ON od.date_id = o.order_date_id
        LEFT JOIN dim_date sd ON sd.date_id = o.ship_date_id
        LEFT JOIN dim_date dd ON dd.date_id = o.delivery_date_id
        WHERE (sd.full_date IS NOT NULL AND sd.full_date < od.full_date)
           OR (dd.full_date IS NOT NULL AND sd.full_date IS NOT NULL
               AND dd.full_date < sd.full_date)
        """,
    ),
    (
        "only Delivered orders carry fulfillment dates",
        """
        SELECT order_id FROM fact_orders
        WHERE order_status <> 'Delivered'
          AND (ship_date_id IS NOT NULL OR delivery_date_id IS NOT NULL)
        """,
    ),
]


def main():
    try:
        conn = psycopg2.connect(**CONN)
    except psycopg2.Error as e:
        print(f"FAIL: could not connect to database: {e}")
        return 1

    failures = 0
    cur = conn.cursor()
    for label, query in CHECKS:
        cur.execute(query)
        offenders = cur.fetchall()
        if offenders:
            failures += 1
            sample = ", ".join(str(r[0]) for r in offenders[:5])
            print(f"FAIL: {label} — {len(offenders)} offending row(s): {sample}")
        else:
            print(f"ok:   {label}")

    conn.close()
    if failures:
        print(f"\n{failures} check(s) failed")
        return 1
    print("\nall checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
