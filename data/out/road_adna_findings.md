# What ROAD already records about ancient DNA

Pulled with roadDB on 2026-11-06 (ROAD snapshot is regularly updated, so counts will drift).

- 2127 localities, 29087 assemblages, 7802 human-remains rows, 15245 dates.
- `locality_id` is the human-readable site name (e.g. "Chagyrskaya", "Denisova Central chamber"), so there is a name field for string matching. All localities have coordinates.
- aDNA is only a category code: `human_remains_category == "S"` (sediment containing human aDNA). 8 rows, 5 localities:
  Chagyrskaya, Denisova Central chamber, Denisova East chamber, El Sidrón, Trou Al Wesse.
  All are Neanderthal or Denisovan sediment DNA. No sample IDs, no publications, no dates beyond the assemblage age range.
- So ROAD cannot serve as a sample-level check. At most these 5 sites are a small sanity check for whichever AADR rows turn up near them.
