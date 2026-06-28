# Handoff

## 2026-06-29 — Fix classification & validation in `build_catalogue.py`

The script ran green and printed "Validation OK", but that was hollow — the
output was full of mislabelled products. Found and fixed five defects.

### Problems
1. **Substring matching** in `classify()` — `"ball"` matched inside
   `"basketball"`, `"mat"` inside `"automatic"`, `"cap"` inside `"Capri"`.
2. **`Balls` was a catch-all dumping ground** — Basketball/Balls held
   "Wristband", "Socks", "Bracelet", "Body-Paint", "Rescue Squad", "Wooden Door".
3. **No accessory filter** — core buckets filled with peripherals:
   "Tennis Shoe Lace", "Cricket Bat Tape", "Bicycle Brake Lever Cover".
4. **`validate()` was tautological** — stored `classify()`'s result then
   asserted `classify() == stored`; could never fail.
5. **Not reproducible** — `SEED` only drove brand/descriptor choice;
   ProductForge samples at `temperature=0.9` with no torch seed.

### Fixes
- `classify()` → word-boundary + plural-tolerant matching; Basketball/Balls
  keyword changed to `basketball`.
- `is_core_noise()` — head-noun allowlist (strips trailing prepositional
  phrases + size/colour/audience/sport qualifiers; keeps a name only if its
  head noun is the bucket's product). Peripheral buckets (Accessories / Apparel
  / Training Gear) are exempt by design.
- `validate()` rewritten with independent post-conditions (head-noun, brand
  pool membership, brand/name agreement) — it can now actually fail.
- Seeded torch in `build()`; two runs now produce a byte-identical
  `products.json`.

`products.json` regenerated and revalidated (400 products, reproducible).

### Open items / tradeoffs
- **Variety vs cleanliness:** strict cleanup pushed several core buckets onto
  the clean template fallback (e.g. Basketball/Balls = PF 1 / template 9), so
  names are cleaner but more formulaic (`{Brand} {Descriptor} Basketball`).
  Lever to loosen: relax the head-noun rule or add more descriptors.
- **Niche brand leak (out of scope):** one name leaked a real brand —
  "Swim Goggles ... by Bling2O". `_BANNED` covers big names but not niche ones.
