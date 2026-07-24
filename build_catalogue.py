"""
Build the product catalogue for the sports-retail dataset using ProductForge.

ProductForge generates brand-safe, on-topic product names but only conditions at
SPORT level, while this store buckets products by PRODUCT TYPE (Cricket -> Bats,
Balls, Pads...). This adapter bridges that:

  for each (sport, product_type):
    1. drive ProductForge with a product-type seed to steer the output
    2. keep only names that classify into this exact bucket, AND — for core
       product buckets — drop peripherals/add-ons (covers, laces, keychains,
       bike parts, "X Socks/Wristband"...) that aren't the product itself
    3. top up any shortfall with a realistic template (ProductForge starves
       minority types like gloves/pads and vague ones like Apparel/Accessories)
    4. prepend a coined brand from a reusable pool

Generation is seeded (python + torch) so re-running yields the same catalogue.

Output: products.json (a static catalogue). generate_db.py reads that, so the
DB build stays light (no torch). Re-run this only when you want a fresh catalogue.

Run with the ProductForge venv (it has torch + the model):
  ../productforge/.venv/Scripts/python.exe build_catalogue.py
"""

from __future__ import annotations

import json
import random
import re
import sys
from pathlib import Path

# ProductForge lives in a sibling repo; import it + steer the model from here.
_PF_SRC = Path(__file__).parent.parent / "productforge" / "src"
sys.path.insert(0, str(_PF_SRC))

from productforge.brand import create_brand
from productforge.generator import generate_products

import config

OUTPUT = Path(__file__).parent / "products.json"
SEED = 42

# ── Coined brand pool (reusable, so brand-level dashboard aggregation is real) ──
BRANDS = [
    "Apex", "Stryde", "Forge", "Greenline", "Tidal", "Cadence",
    "Vanta", "Northgate", "Halcyon", "Kestrel", "Summit", "Volt",
]

# ── Bucket rules per sport, PRIORITY-ORDERED (specific first, generic "ball"
#    last) so e.g. "Basketball Hoop" classifies as Hoops, not Balls. ───────────
# sport -> [(type, [match keywords], pf seed, template noun)]
PF_SUB = {
    "Cricket": "cricket", "Soccer": "soccer", "Basketball": "basketball",
    "Tennis": "tennis", "Golf": "golf", "Swimming": "swimming",
    "Running": "running", "Cycling": "cycling", "Gym/Fitness": "gym",
}

BUCKETS: dict[str, list[tuple]] = {
    "Cricket": [
        ("Helmets", ["helmet"], "Cricket Helmet", "Cricket Helmet"),
        ("Pads", ["pad", "guard"], "Batting Pad", "Batting Pads"),
        ("Gloves", ["glove", "mitt"], "Batting Glove", "Batting Gloves"),
        ("Bats", ["bat"], "Cricket Bat", "Cricket Bat"),
        ("Balls", ["ball"], "Cricket Ball", "Cricket Ball"),
    ],
    "Soccer": [
        ("Boots", ["boot", "cleat"], "Soccer Cleat", "Soccer Cleats"),
        ("Jerseys", ["jersey", "kit", "shirt"], "Soccer Jersey", "Soccer Jersey"),
        ("Training Gear", ["training", "cone", "agility", "rebounder", "ladder", "goal", "net"],
         "Soccer Training", "Training Cones"),
        ("Balls", ["ball"], "Soccer Ball", "Soccer Ball"),
    ],
    "Basketball": [
        ("Hoops", ["hoop", "backboard", "rim", "net"], "Basketball Hoop", "Basketball Hoop"),
        ("Shoes", ["shoe", "sneaker", "trainer"], "Basketball Shoe", "Basketball Shoes"),
        ("Jerseys", ["jersey", "shorts", "shirt"], "Basketball Jersey", "Basketball Jersey"),
        # "basketball" (not "ball") — with word-boundary matching the sport name is
        # the ball itself; bare "ball" never appears in a basketball product name.
        ("Balls", ["basketball"], "Basketball", "Basketball"),
    ],
    "Tennis": [
        ("Racquets", ["racquet", "racket"], "Tennis Racquet", "Tennis Racquet"),
        ("Shoes", ["shoe", "sneaker", "trainer"], "Tennis Shoe", "Tennis Shoes"),
        ("Bags", ["bag", "backpack"], "Tennis Bag", "Tennis Bag"),
        ("Balls", ["ball"], "Tennis Ball", "Tennis Balls"),
    ],
    "Golf": [
        ("Clubs", ["club", "driver", "iron", "putter", "wedge", "hybrid"], "Golf Club", "Golf Club"),
        ("Bags", ["bag", "backpack"], "Golf Bag", "Golf Bag"),
        ("Apparel", ["polo", "glove", "hat", "cap", "jacket", "shirt", "short", "pant", "apparel"],
         "Golf Glove", "Golf Polo"),
        ("Accessories", ["tee", "marker", "towel", "umbrella", "cover", "headcover", "grip", "stencil", "divot"],
         "Golf Tee", "Golf Tee Set"),
        ("Balls", ["ball"], "Golf Ball", "Golf Balls"),
    ],
    "Swimming": [
        ("Goggles", ["goggle", "mask"], "Swim Goggles", "Swim Goggles"),
        ("Caps", ["cap"], "Swim Cap", "Swim Cap"),
        ("Fins", ["fin", "flipper"], "Swim Fins", "Swim Fins"),
        ("Kickboards", ["kickboard", "board"], "Kickboard", "Kickboard"),
        ("Swimwear", ["swimsuit", "swimwear", "trunk", "jammer", "wetsuit", "suit"], "Swimsuit", "Swimsuit"),
    ],
    "Running": [
        ("Shoes", ["shoe", "sneaker", "trainer"], "Running Shoe", "Running Shoes"),
        ("Watches", ["watch", "gps", "tracker", "monitor"], "Running Watch", "Running Watch"),
        ("Apparel", ["shirt", "short", "sock", "jacket", "tight", "vest", "cap", "hat", "glove", "apparel"],
         "Running Shirt", "Running Shirt"),
        ("Accessories", ["belt", "band", "holder", "bottle", "light", "strap", "pack", "bib", "pouch"],
         "Running Belt", "Running Belt"),
    ],
    "Cycling": [
        ("Helmets", ["helmet"], "Cycling Helmet", "Cycling Helmet"),
        ("Apparel", ["jersey", "short", "glove", "jacket", "bib", "sock", "apparel"], "Cycling Jersey", "Cycling Jersey"),
        ("Accessories", ["pump", "light", "lock", "bottle", "saddle", "pedal", "grip", "tire", "tube", "bell", "mount", "rack"],
         "Bike Pump", "Bike Pump"),
        ("Bikes", ["bike", "bicycle", "cycle"], "Bicycle", "Bike"),
    ],
    "Gym/Fitness": [
        ("Benches", ["bench"], "Weight Bench", "Weight Bench"),
        ("Mats", ["mat"], "Yoga Mat", "Exercise Mat"),
        ("Resistance Bands", ["resistance", "band"], "Resistance Band", "Resistance Band"),
        ("Weights", ["weight", "dumbbell", "kettlebell", "barbell", "plate"], "Dumbbell", "Dumbbell Set"),
    ],
}

DESCRIPTORS = ["Pro", "Elite", "Match", "Junior", "Lightweight", "Tour",
               "Premium", "Classic", "Performance", "Team"]

# Store-side safety net for real-world IP that ProductForge's structural team
# fictionalization can't catch: player names and numbered-jersey merch ("#5 ...").
_BANNED = re.compile(
    r"#\s?\d|\b("
    r"Messi|Ronaldo|Neymar|Mbappe|Lebron|Curry|Giannis|Jordan|Kobe|Durant|"
    r"Madrid|Barcelona|Bayern|Juventus|Chelsea|Arsenal|Liverpool|Tottenham|"
    r"Lakers|Knicks|Celtics|Warriors|Yankees|"
    r"Nike|Adidas|Puma|Reebok|Wilson|Spalding|Schwinn|Yamaha|Callaway|Titleist|"
    r"NBA|NFL|FIFA|NCAA|NHL|MLB)\b",
    re.IGNORECASE,
)


# Buckets that legitimately hold peripheral/add-on items — never noise-filtered.
# They're deliberate grab-bags (a golf "Accessory" can be a tee, towel, marker…),
# so the core-product head-noun test below doesn't apply to them.
_PERIPHERAL_BUCKETS = {"Accessories", "Apparel", "Training Gear"}

# Trailing words that are size / colour / audience / sport / marketing modifiers
# rather than the product noun. Stripped from the tail before reading the head
# noun, so "Soccer Ball Size 5 for Kids" still resolves to "ball", and
# "Kickboard for Swimming" to "kickboard".
_QUALIFIERS = frozenset((
    "for", "with", "and", "the", "of", "in", "by", "to", "a", "an", "or",
    "set", "sets", "pack", "packs", "kit", "size", "sized", "sizes",
    "pair", "pairs", "pc", "pcs", "piece", "pieces", "new", "official",
    "men", "mens", "man", "women", "womens", "woman", "kids", "kid", "youth",
    "adult", "adults", "junior", "boys", "boy", "girls", "girl", "unisex",
    "toddler", "baby", "children", "childrens", "mens", "ladies",
    "black", "white", "blue", "red", "green", "yellow", "pink", "purple",
    "grey", "gray", "orange", "silver", "gold", "navy", "teal", "brown",
    "small", "medium", "large", "xl", "xxl", "xxxl", "xs", "s", "m", "l",
    "indoor", "outdoor", "portable", "foldable", "adjustable", "waterproof",
    "premium", "deluxe", "professional", "lightweight", "durable", "mini",
    "travel", "home", "reusable", "automatic", "wireless", "long", "short",
    "training", "practice", "sport", "sports", "color", "colour",
    "swim", "swimming", "cricket", "soccer", "tennis", "golf", "running",
    "cycling", "gym", "fitness",
))


def _has_kw(low: str, kw: str) -> bool:
    """Whole-word keyword match, plural-tolerant ('goggle' matches 'goggles',
    'watch' matches 'watches') but boundary-anchored so 'ball' never matches
    inside 'basketball'."""
    return re.search(rf"\b{re.escape(kw)}(?:es|s)?\b", low) is not None


def _head_noun(name: str) -> str:
    """The product noun a name is really about: its last alphabetic token after
    cutting any trailing prepositional phrase and dropping trailing qualifiers.
    'Cricket Bat Covers for Men' -> 'covers'; 'Speedometer for Road Bike' ->
    'speedometer'; 'Ball with Pump' -> 'ball'."""
    toks = re.findall(r"[a-z]+", name.lower())
    for prep in ("for", "with"):           # the head noun precedes "... for/with X"
        if prep in toks[1:]:
            toks = toks[:toks.index(prep, 1)]
    while toks and (len(toks[-1]) <= 1 or toks[-1] in _QUALIFIERS):
        toks.pop()
    return toks[-1] if toks else ""


def classify(name: str, sport: str) -> str | None:
    """Return the bucket a name belongs to (priority order), or None."""
    low = name.lower()
    for bucket_type, kws, _seed, _noun in BUCKETS[sport]:
        if any(_has_kw(low, kw) for kw in kws):
            return bucket_type
    return None


def is_core_noise(name: str, sport: str, bucket_type: str) -> bool:
    """True if `name` is a peripheral/add-on wrongly landing in a *core* bucket
    — i.e. its head noun isn't the bucket's product. 'Cricket Bat Tape' (head
    'tape') and 'Basketball Stickers' (head 'stickers') are noise; 'Cricket Bat'
    and 'Basketballs' are not."""
    if bucket_type in _PERIPHERAL_BUCKETS:
        return False
    head = _head_noun(name)
    kws = next(kw for bt, kw, _s, _n in BUCKETS[sport] if bt == bucket_type)
    return not any(_has_kw(head, kw) for kw in kws)


def tidy(name: str) -> str:
    """Collapse spaces and immediate duplicate words from brand assembly."""
    name = re.sub(r"\s{2,}", " ", name).strip()
    name = re.sub(r"\b(\w+)(\s+\1\b)+", r"\1", name, flags=re.IGNORECASE)
    return name


def targets(total: int, n_buckets: int) -> list[int]:
    """Split `total` products across buckets as evenly as possible."""
    base, rem = divmod(total, n_buckets)
    return [base + (1 if i < rem else 0) for i in range(n_buckets)]


def build() -> list[dict]:
    rng = random.Random(SEED)
    # ProductForge samples (do_sample=True); seed torch so the catalogue is
    # reproducible across runs, matching the python-side rng above.
    try:
        import torch
        torch.manual_seed(SEED)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(SEED)
    except ImportError:
        pass

    catalogue: list[dict] = []
    seen: set[str] = set()
    report: list[str] = []

    neutral = create_brand("X", "sports", "cricket", root_morpheme=None,
                           preferred_suffix=None, uses_version_numbers=False)

    for sport, cat in config.CATEGORIES.items():
        buckets = BUCKETS[sport]
        pf_sub = PF_SUB[sport]
        per = targets(cat["products"], len(buckets))
        # Re-point the neutral brand's taxonomy to this sport (subcategory drives gen)
        neutral.subcategory = pf_sub

        for (bucket_type, kws, seed, noun), want in zip(buckets, per):
            chosen: list[str] = []

            # 1) ProductForge, steered toward the product type. Over-generate:
            #    dropping peripherals (covers/laces/parts) thins the yield, so ask
            #    for plenty and let the template fallback cover any shortfall.
            pf_names = generate_products("sports", pf_sub, neutral,
                                         n=want * 2 + 8, seed=seed)
            for body in pf_names:
                if len(chosen) >= want:
                    break
                if (classify(body, sport) != bucket_type
                        or is_core_noise(body, sport, bucket_type)
                        or _BANNED.search(body)):
                    continue
                brand = rng.choice(BRANDS)
                name = tidy(f"{brand} {body}")
                if name.lower() in seen:
                    continue
                seen.add(name.lower())
                chosen.append(name)
            pf_filled = len(chosen)

            # 2) Template fallback for the shortfall
            attempts = 0
            while len(chosen) < want and attempts < want * 50:
                attempts += 1
                brand = rng.choice(BRANDS)
                desc = rng.choice(DESCRIPTORS)
                name = tidy(f"{brand} {desc} {noun}")
                if (classify(name, sport) != bucket_type
                        or is_core_noise(name, sport, bucket_type)
                        or name.lower() in seen):
                    continue
                seen.add(name.lower())
                chosen.append(name)

            for name in chosen:
                catalogue.append({
                    "product_name": name, "brand": name.split()[0],
                    "category": sport, "subcategory": bucket_type,
                })
            report.append(f"  {sport:12s}/{bucket_type:16s} {len(chosen):3d}/{want:<3d}"
                          f"  (PF {pf_filled}, template {len(chosen)-pf_filled})")

    print("Per-bucket fill (PF vs template):")
    print("\n".join(report))
    return catalogue


def validate(catalogue: list[dict]) -> None:
    expected = sum(c["products"] for c in config.CATEGORIES.values())
    assert len(catalogue) == expected, f"size {len(catalogue)} != {expected}"
    for row in catalogue:
        name, sport, sub = row["product_name"], row["category"], row["subcategory"]
        # Independent post-conditions: these check properties of `name` itself,
        # not the value we happened to store, so they can actually fail.
        assert sub in {b[0] for b in BUCKETS[sport]}, f"unknown bucket: {row}"
        assert classify(name, sport) == sub, f"misclassified ({classify(name, sport)}): {row}"
        assert not is_core_noise(name, sport, sub), f"peripheral in core bucket: {name}"
        assert not _BANNED.search(name), f"real IP leak: {name}"
        assert row["brand"] in BRANDS, f"brand not in pool: {row}"
        assert name.split()[0] == row["brand"], f"brand/name mismatch: {row}"
    names = [r["product_name"].lower() for r in catalogue]
    assert len(set(names)) == len(names), "duplicate product names"
    print(f"\nValidation OK: {len(catalogue)} products, all bucket-coherent, "
          f"no peripherals in core buckets, 0 real-IP, all unique.")


def main() -> None:
    catalogue = build()
    validate(catalogue)
    OUTPUT.write_text(json.dumps(catalogue, indent=2), encoding="utf-8")
    print(f"Wrote {OUTPUT}  ({len(catalogue)} products)")


if __name__ == "__main__":
    main()
