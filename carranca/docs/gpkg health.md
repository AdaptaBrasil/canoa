# GeoPackage Frame data Health Score
__A discussion with Claude__
2026-05

---
Four data quality indexes are evaluated to compute the health score.

- **Invalid geometries**
    The most critical issue. Malformed shapes break spatial operations such as joins, overlays,
    and buffers entirely.
- **Missing CRS**  Nearly as severe. Without a Coordinate Reference System (CRS),
    any projection or overlay operation will produce silently wrong results.
- **Empty geometries**  Rows where the geometry column exists but holds no shape,
    causing silent data loss in spatial analyses.
- **Null values**  The least critical issue. Attribute gaps reduce analytical
    completeness but leave the layer spatially usable.


Each issue contributes a *fractional penalty* proportional to how widespread it is:

```
penalty_i = (affected / total_possible) × weight_i
```

Then the final score is:

```
score = (1 − Σ penalties / Σ weights) × 100
```

| Issue | Weight | Rationale |
|---|---|---|
| `invalid_geometries` | **10** | Breaks `sjoin`, `overlay`, `buffer` — catastrophic |
| `missing_crs` | **8** | Silent wrong results on any projection operation |
| `empty_geometries` | **6** | Data loss; geometry column exists but is useless |
| `null_values` | **4** | Attribute gaps; layer still spatially usable |

A file with no issues scores **100 %**. A file where every row has an invalid geometry scores close to **0 %**
(that component alone drags it to ~64 % if everything else is clean, because invalid geom carries 10/28 of the weight).
 All four problems at full severity → **0 %**.

Code (```.\carranca\private\spd_analysis.py```)
```python
def _health_score(gdf: gpd.GeoDataFrame) -> dict:
    n = len(gdf)  # total number of features (geometries)

    # Raw counts / flags
    invalid_geom   = int((~gdf.is_valid).sum())
    empty_geom     = int(gdf.geometry.is_empty.sum())
    missing_crs    = int(gdf.crs is None)          # 0 or 1
    null_values    = int(gdf.isna().sum().sum())

    # Weights (1–10 scale, higher = more damaging)
    W_INVALID_GEOM = 10   # breaks spatial ops entirely
    W_EMPTY_GEOM   =  6   # silent data loss
    W_MISSING_CRS  =  8   # projections / overlays fail
    W_NULL_VALUES  =  4   # attribute gaps, less critical

    TOTAL_WEIGHT = W_INVALID_GEOM + W_EMPTY_GEOM + W_MISSING_CRS + W_NULL_VALUES  # 28

    def _penalty(count: int, weight: int, max_count: int) -> float:
        """Fractional penalty [0.0 – weight] for one issue."""
        if max_count == 0:
            return 0.0
        ratio = min(count / max_count, 1.0)   # cap at 100 %
        return ratio * weight

    penalties = (
        _penalty(invalid_geom, W_INVALID_GEOM, n)
        + _penalty(empty_geom,   W_EMPTY_GEOM,   n)
        + _penalty(missing_crs,  W_MISSING_CRS,  1)   # binary: 0 or 1
        + _penalty(null_values,  W_NULL_VALUES,  n * len(gdf.columns))
    )

    score = round((1 - penalties / TOTAL_WEIGHT) * 100, 1)

    return {
        "score": score,
        "count": n,
        "issues": {
            "invalid_geometries": {"count": invalid_geom, "weight": W_INVALID_GEOM},
            "empty_geometries":   {"count": empty_geom,   "weight": W_EMPTY_GEOM},
            "missing_crs":        {"count": missing_crs,  "weight": W_MISSING_CRS},
            "null_values":        {"count": null_values,  "weight": W_NULL_VALUES},
        },
    }
```
---
<small>_eof_</small>
