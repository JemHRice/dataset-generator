# =============================================================================
# SPORTS RETAIL DATABASE — CONFIGURATION FILE
# =============================================================================
#
# This is the only file you need to edit to customise your database.
# Once you're happy with your settings, open PowerShell and run:
#
#     python generate_db.py
#
# The script will build the entire database based on what you set here.
#
# TIPS:
#   - Lines starting with # are comments — they're ignored by the script
#   - Text values must stay inside their quote marks: "Like This"
#   - Numbers should have no quote marks: 42  not  "42"
#   - Don't delete any section headings or variable names
# =============================================================================


# -----------------------------------------------------------------------------
# REPRODUCIBLE DATA
# -----------------------------------------------------------------------------
# By default, every run produces a unique random dataset.
# If you want the exact same data every time (useful for sharing or comparing),
# set USE_FIXED_SEED to True.

USE_FIXED_SEED = True
RANDOM_SEED = 42  # Only matters if USE_FIXED_SEED is True above


# -----------------------------------------------------------------------------
# DATA VOLUMES
# -----------------------------------------------------------------------------
# Controls how much data gets generated.
# Larger numbers = more realistic data but slower to generate.
#
# Rough timing guide on a standard laptop:
#   100,000 orders  →  ~1 minute
#   400,000 orders  →  ~3 minutes
#   1,000,000 orders → ~8 minutes

TARGET_ORDERS = 400000  # Total number of customer orders to generate
TARGET_ORDER_ITEMS = (
    1000000  # Shown in the summary — actual count will be ~3.4x TARGET_ORDERS
)
NUM_STORES = 50  # Number of retail store locations
NUM_SALESPERSONS = 100  # Total sales staff (spread across all stores)
NUM_PRODUCTS = 400  # Total products in the catalogue
NUM_CUSTOMERS = 75000  # Size of the customer pool (unique customer IDs)


# -----------------------------------------------------------------------------
# CUSTOMER BEHAVIOUR
# -----------------------------------------------------------------------------
# Controls how the customer base is built and how repeat-purchasing behaves.
#
# CUSTOMER_INITIAL_BASE_FRACTION — share of customers who already exist on the
#   first day (START_DATE). The rest are "acquired" gradually across the date
#   range, so cohort/acquisition analysis is meaningful. 0.40 = 40% existing.
#
# CUSTOMER_REPEAT_SIGMA — spread of how often customers buy. Each customer gets
#   a hidden frequency weight drawn from a lognormal distribution; higher sigma
#   means a few customers buy a LOT while most buy rarely (more skewed). Typical
#   range 0.6 (fairly even) to 1.4 (very skewed). 1.0 is a realistic default.

CUSTOMER_INITIAL_BASE_FRACTION = 0.40
CUSTOMER_REPEAT_SIGMA = 1.0


# -----------------------------------------------------------------------------
# DATE RANGE
# -----------------------------------------------------------------------------
# The time period your sales data covers.
# Format is: (YEAR, MONTH, DAY)

START_DATE = (2020, 1, 1)
END_DATE = (2024, 12, 31)


# -----------------------------------------------------------------------------
# STATES & TERRITORIES
# -----------------------------------------------------------------------------
# The regions your stores operate in.
#
# "weight" controls how much activity comes from each state.
# Higher weight = more stores and orders from that state.
# Weights are relative — they don't need to add up to any specific number.
#
# To remove a state: delete its block (all 3 lines including the curly braces)
# To add a state: copy an existing block and change the values
#
# The "code" is used in store addresses — keep it short (2-3 letters)

STATES = {
    "New South Wales": {"code": "NSW", "weight": 0.32},
    "Victoria": {"code": "VIC", "weight": 0.26},
    "Queensland": {"code": "QLD", "weight": 0.20},
    "Western Australia": {"code": "WA", "weight": 0.11},
    "South Australia": {"code": "SA", "weight": 0.07},
    "Tasmania": {"code": "TAS", "weight": 0.02},
    "ACT": {"code": "ACT", "weight": 0.015},
    "Northern Territory": {"code": "NT", "weight": 0.01},
}


# -----------------------------------------------------------------------------
# STORE LOCATIONS
# -----------------------------------------------------------------------------
# Cities and suburbs where stores can be located, grouped by state code.
# The state codes here must match the "code" values in STATES above.
#
# Add or remove suburb names freely — just keep them as "quoted strings"
# separated by commas inside the square brackets.

SUBURBS_BY_STATE = {
    "NSW": [
        "Sydney",
        "Newcastle",
        "Wollongong",
        "Central Coast",
        "Lismore",
        "Coffs Harbour",
    ],
    "VIC": [
        "Melbourne",
        "Geelong",
        "Ballarat",
        "Bendigo",
        "Shepparton",
        "Latrobe Valley",
    ],
    "QLD": [
        "Brisbane",
        "Gold Coast",
        "Sunshine Coast",
        "Cairns",
        "Townsville",
        "Toowoomba",
    ],
    "WA": ["Perth", "Fremantle", "Mandurah", "Bunbury", "Albany"],
    "SA": ["Adelaide", "Mount Gambier", "Whyalla"],
    "TAS": ["Hobart", "Launceston"],
    "ACT": ["Canberra"],
    "NT": ["Darwin"],
}


# -----------------------------------------------------------------------------
# SPORT CATEGORIES & PRODUCTS
# -----------------------------------------------------------------------------
# The sports your store sells, and the products within each sport.
#
# Each category has:
#   subcategories — the types of products within that sport
#   products      — how many products to generate for this category
#   margin        — pricing multiplier (1.5 means 50% markup, 2.0 means 100% markup)
#
# The total "products" values across all categories should roughly equal
# NUM_PRODUCTS set above. If they don't match exactly, the script adjusts automatically.
#
# To remove a sport: delete its entire block
# To add a sport: copy an existing block and fill in your values

CATEGORIES = {
    "Cricket": {
        "subcategories": ["Bats", "Balls", "Pads", "Gloves", "Helmets"],
        "products": 60,
        "margin": 1.5,
    },
    "Soccer": {
        "subcategories": ["Balls", "Boots", "Jerseys", "Training Gear"],
        "products": 50,
        "margin": 1.45,
    },
    "Basketball": {
        "subcategories": ["Balls", "Hoops", "Shoes", "Jerseys"],
        "products": 40,
        "margin": 1.4,
    },
    "Tennis": {
        "subcategories": ["Racquets", "Balls", "Shoes", "Bags"],
        "products": 40,
        "margin": 1.55,
    },
    "Golf": {
        "subcategories": ["Clubs", "Bags", "Balls", "Apparel", "Accessories"],
        "products": 50,
        "margin": 1.6,
    },
    "Swimming": {
        "subcategories": ["Goggles", "Caps", "Swimwear", "Fins", "Kickboards"],
        "products": 40,
        "margin": 1.35,
    },
    "Running": {
        "subcategories": ["Shoes", "Apparel", "Watches", "Accessories"],
        "products": 40,
        "margin": 1.5,
    },
    "Cycling": {
        "subcategories": ["Bikes", "Helmets", "Apparel", "Accessories"],
        "products": 40,
        "margin": 1.45,
    },
    "Gym/Fitness": {
        "subcategories": ["Weights", "Resistance Bands", "Mats", "Benches"],
        "products": 40,
        "margin": 1.4,
    },
}


# -----------------------------------------------------------------------------
# SHIPPING METHODS
# -----------------------------------------------------------------------------
# The delivery options available to customers.
#
# Each method has:
#   name      — display name shown in the data
#   carrier   — the shipping company
#   min_days  — fastest possible delivery (0 = same day)
#   max_days  — slowest possible delivery
#   cost      — flat fee in dollars (use 0.00 for free)

SHIPPING_METHODS = [
    {
        "name": "Standard Post",
        "carrier": "Australia Post",
        "min_days": 5,
        "max_days": 8,
        "cost": 7.95,
    },
    {
        "name": "Express Post",
        "carrier": "Australia Post",
        "min_days": 2,
        "max_days": 3,
        "cost": 14.95,
    },
    {
        "name": "Same Day",
        "carrier": "Local Courier",
        "min_days": 0,
        "max_days": 1,
        "cost": 24.95,
    },
    {
        "name": "Click & Collect",
        "carrier": "In-Store",
        "min_days": 0,
        "max_days": 0,
        "cost": 0.00,
    },
    {
        "name": "Overnight",
        "carrier": "Express Courier",
        "min_days": 1,
        "max_days": 2,
        "cost": 19.95,
    },
]


# -----------------------------------------------------------------------------
# PROMOTIONAL EVENTS
# -----------------------------------------------------------------------------
# Sales events that boost order volumes and apply discounts during their period.
#
# Each promotion has:
#   name          — the promotion name (appears in your data)
#   start_date    — when the promotion starts: (YEAR, MONTH, DAY)
#   end_date      — when it ends: (YEAR, MONTH, DAY)
#   discount_rate — discount applied to items  (0.20 = 20% off, 0.30 = 30% off)
#   category      — which sport category gets the discount
#                   MUST exactly match a category name from CATEGORIES above
#
# You can have as many or as few promotions as you like.
# Promotions must fall within your START_DATE and END_DATE range above.

PROMOTIONS = [
    {
        "name": "Summer Cricket Sale",
        "start_date": (2020, 12, 1),
        "end_date": (2020, 12, 14),
        "discount_rate": 0.15,
        "category": "Cricket",
    },
    {
        "name": "New Year Fitness Push",
        "start_date": (2021, 1, 1),
        "end_date": (2021, 1, 31),
        "discount_rate": 0.20,
        "category": "Gym/Fitness",
    },
    {
        "name": "Soccer Grand Final Weekend",
        "start_date": (2021, 9, 15),
        "end_date": (2021, 9, 28),
        "discount_rate": 0.25,
        "category": "Soccer",
    },
    {
        "name": "Spring Running Festival",
        "start_date": (2021, 10, 1),
        "end_date": (2021, 10, 10),
        "discount_rate": 0.18,
        "category": "Running",
    },
    {
        "name": "Summer Swimming Special",
        "start_date": (2022, 1, 15),
        "end_date": (2022, 1, 28),
        "discount_rate": 0.20,
        "category": "Swimming",
    },
    {
        "name": "Golf Masters Sale",
        "start_date": (2022, 3, 15),
        "end_date": (2022, 3, 25),
        "discount_rate": 0.22,
        "category": "Golf",
    },
    {
        "name": "Cycling Spring Clearance",
        "start_date": (2023, 9, 1),
        "end_date": (2023, 9, 14),
        "discount_rate": 0.20,
        "category": "Cycling",
    },
    {
        "name": "Tennis Summer Bash",
        "start_date": (2023, 12, 15),
        "end_date": (2024, 1, 5),
        "discount_rate": 0.25,
        "category": "Tennis",
    },
    {
        "name": "Winter Fitness Challenge",
        "start_date": (2024, 6, 1),
        "end_date": (2024, 6, 30),
        "discount_rate": 0.18,
        "category": "Gym/Fitness",
    },
    {
        "name": "End of Season Clearance",
        "start_date": (2024, 11, 1),
        "end_date": (2024, 11, 10),
        "discount_rate": 0.30,
        "category": "Cricket",
    },
]


# -----------------------------------------------------------------------------
# PUBLIC HOLIDAYS
# -----------------------------------------------------------------------------
# National public holidays used to adjust order volumes slightly.
# Format: (YEAR, MONTH, DAY)
#
# These are Australian national holidays 2020-2024.
# Update these if you change your date range or want different holiday patterns.

PUBLIC_HOLIDAYS = [
    (2020, 1, 1),
    (2020, 1, 27),
    (2020, 4, 10),
    (2020, 4, 13),
    (2020, 4, 25),
    (2020, 6, 8),
    (2020, 12, 25),
    (2020, 12, 26),
    (2021, 1, 1),
    (2021, 1, 26),
    (2021, 4, 2),
    (2021, 4, 5),
    (2021, 4, 25),
    (2021, 6, 14),
    (2021, 12, 25),
    (2021, 12, 26),
    (2022, 1, 1),
    (2022, 1, 26),
    (2022, 4, 15),
    (2022, 4, 18),
    (2022, 4, 25),
    (2022, 6, 13),
    (2022, 12, 25),
    (2022, 12, 26),
    (2023, 1, 1),
    (2023, 1, 26),
    (2023, 4, 7),
    (2023, 4, 10),
    (2023, 4, 25),
    (2023, 6, 12),
    (2023, 12, 25),
    (2023, 12, 26),
    (2024, 1, 1),
    (2024, 1, 26),
    (2024, 3, 29),
    (2024, 4, 1),
    (2024, 4, 25),
    (2024, 6, 10),
    (2024, 12, 25),
    (2024, 12, 26),
]
