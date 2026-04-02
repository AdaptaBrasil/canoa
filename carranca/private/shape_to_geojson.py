"""
shape_to_geojson.py  —  Canoa
Converts a Shapefile (.shp/.dbf/.shx/.prj) to GeoJSON (EPSG:4326).


Equipe da Canoa -- 2026 + Anthropic Claude
mgd 2026-03-24
"""

# cSpell:words pyogrio geopandas reproject reprojection reprojecting serialisable miny maxx maxy indentação

import os
import sys
import json

from pathlib import Path


EPSG_WGS84 = 4326
# WGS 84 the most common CRS for global data (latitude/longitude) and is the standard for GeoJSON.
TARGET_CRS = f"EPSG:{EPSG_WGS84}"  # Coordinate Reference System


def _require(package: str, pip_name: str | None = None) -> None:
    import importlib

    if importlib.util.find_spec(package) is None:
        pip = pip_name or package
        print(f"[erro] Pacote '{package}' não encontrado.  Execute:  pip install {pip}", file=sys.stderr)
        sys.exit(1)


_require("geopandas")
_require("pyogrio")
import geopandas as gpd  # noqa: E402  (after the check above)


def _load_shapefile(shp_path: Path, encoding: str) -> gpd.GeoDataFrame:
    """Read the shapefile using pyogrio as the backend."""
    gdf = gpd.read_file(shp_path, engine="pyogrio", encoding=encoding)
    return gdf


def _inspect(gdf: gpd.GeoDataFrame, shp_path: Path) -> dict:
    """Return a JSON-serialisable summary of the layer and print it."""

    bbox = gdf.total_bounds  # (minx, miny, maxx, maxy)
    summary = {
        "file": shp_path.name,
        "features": len(gdf),
        "crs": str(gdf.crs) if gdf.crs else None,
        "geometry": gdf.geom_type.value_counts().to_dict(),
        "columns": list(gdf.columns),
        "bbox": {
            "xmin": round(float(bbox[0]), 6),
            "ymin": round(float(bbox[1]), 6),
            "xmax": round(float(bbox[2]), 6),
            "ymax": round(float(bbox[3]), 6),
        },
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return summary


def _reproject(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    # CRSs that are equivalent to EPSG:4326 for practical purposes:
    # same ellipsoid, same axes — reprojecting would waste time with no
    # meaningful coordinate change (< 1 mm difference).
    _EQUIVALENT_TO_4326 = {
        # c Spell:disable
        EPSG_WGS84,  # WGS 84
        4674,  # SIRGAS 2000  (GRS 1980, aligned to ITRF)
        4170,  # SIRGAS 1995  (same ellipsoid, legacy code)
        4759,  # NAD83(NSRS2007)
        4152,  # NAD83(HARN)
        # c Spell:enable
    }

    if gdf.crs is None:
        minx, miny, maxx, maxy = gdf.total_bounds
        # Heuristic: Coordinates in degrees are usually within [-180, 180].
        # If values are large, it is likely projected (meters).
        if minx < -180 or maxx > 180 or miny < -90 or maxy > 90:
            print(f"[aviso] Shapefile sem CRS. As coordenadas parecem estar projetadas (metros?)")
            print(f"        Bounds: ({minx:.1f}, {miny:.1f}, {maxx:.1f}, {maxy:.1f})")
            print(f"        Assumindo {TARGET_CRS} mesmo assim. O GeoJSON pode ficar inválido.")
        else:
            print(f"[aviso] Shapefile sem CRS definido — assumindo {TARGET_CRS}.")

        gdf = gdf.set_crs(TARGET_CRS)
        return gdf

    epsg = gdf.crs.to_epsg()

    if epsg in _EQUIVALENT_TO_4326:
        if epsg != EPSG_WGS84:
            print(
                f"[info]  {gdf.crs} is equivalent to {TARGET_CRS} — skipping reprojection, reassigning CRS."
            )
            gdf = gdf.set_crs(TARGET_CRS, allow_override=True)
    else:
        print(f"[info]  Reprojecting {gdf.crs} → {TARGET_CRS}")
        gdf = gdf.to_crs(TARGET_CRS)

    return gdf


def convert(
    shp_path: Path,
    out_path: Path,
    indent: int,
    encoding: str,
    info_only: bool,
    redo_shx: bool,
) -> dict:

    # check if shx file exists, if not recreate
    shx_path = shp_path.with_suffix(".shx")
    force_shx = not shx_path.exists() and not redo_shx
    if force_shx:
        print(f"[aviso] Arquivo de índice .shx ausente: {shx_path.name}, recriando…")
        redo_shx = True

    if redo_shx:
        # Must be set before loading the file
        os.environ["SHAPE_RESTORE_SHX"] = "YES"

    print(f"[info]  Lendo {shp_path} …")
    gdf = _load_shapefile(shp_path, encoding)

    info = _inspect(gdf, shp_path)

    if info_only:
        if os.environ.get("SHAPE_RESTORE_SHX") == "YES":
            print("[info]  Modo --info: GeoJSON não gerado (índice .shx verificado/restaurado).")
        else:
            print("[info]  Modo --info: nenhum arquivo gerado.")
        return info

    gdf = _reproject(gdf)

    print(f"[info]  Gravando {out_path} …")
    # Write via pyogrio directly — fast, no in-memory round-trip.
    # Indentation is cosmetic: apply it only when explicitly requested
    # (indent > 0) as a single re-format pass over the finished file.

    gdf.to_file(out_path, driver="GeoJSON", engine="pyogrio")

    if indent > 0:
        print(f"[info]  Formatando com indentação {indent} {out_path}  …")
        # Re-format in place.  json.load/dump reads from disk, so peak
        # RAM stays proportional to the file, not a second full copy.
        with out_path.open(encoding="utf-8") as fh:
            data = json.load(fh)
        out_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=indent),
            encoding="utf-8",
        )

    size_kb = out_path.stat().st_size / 1024
    print(f"[ok]    {len(gdf):,} features  →  {out_path}  ({size_kb:,.1f} KB)\n")

    return info


# eof
