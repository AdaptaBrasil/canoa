"""
Module for analyzing spatial data from GeoPackage (.gpkg) files using GeoPandas and Pyogrio for fast I/O.


mgd 2026.05.07
"""

import pyogrio
import pandas as pd
import geopandas as gpd

from io import BytesIO
from typing import Tuple, List
from datetime import datetime

from ..helpers.py_helper import now_as_iso, same_entry
from ..helpers.types_helper import Usual_Dict, Primitive

# cspell:words ffname pyogrio gpkg sjoin geospatial

SPD_MODULE_VERSION = "1.0"

SPD_FORMAT_GPKG = "GPKG"  # GeoPackage
SPD_EXT_GPKG = ["gpkg"]
SPD_FORMAT_SHP = "SHP"  # ESRI Shapefile
SPD_EXT_SHP = ["shp"]  # ESRI Shapefile
SPD_FORMAT_GEOJSON = "GeoJSON"  # GeoJSON
SPD_EXT_GEOJSON = ["geojson", "json"]  # GeoJSON

SPD_VALUES_FROM_ALL_FIELDS = ["*"]

_SPD_FORMAT_FILE = "FILE"  # Internal use
_SPD_FILE_NAME_SEP = "|"  # don't use any valid file path name char (a..z, :,\, ..)

SPD_FORMAT_GPKG = "GPKG"
SPD_EXT_GPKG = ["gpkg"]

SPD_FORMAT_SHP = "SHP"
SPD_EXT_SHP = ["shp"]

SPD_FORMAT_GEOJSON = "GeoJSON"
SPD_EXT_GEOJSON = ["geojson", "json"]

# Unified list of (format, extensions)
SPD_FORMATS = [
    (SPD_FORMAT_GPKG, SPD_EXT_GPKG),
    (SPD_FORMAT_SHP, SPD_EXT_SHP),
    (SPD_FORMAT_GEOJSON, SPD_EXT_GEOJSON),
]


def spd_file_format(file_ext: str):
    """
    Mapeia extensões de arquivos espaciais para seus formatos (GPKG, SHP, GeoJSON).
    Retorna o formato correspondente ou None.
    """
    file_ext = file_ext.lower().lstrip(".")
    for fmt, ext_list in SPD_FORMATS:
        if file_ext in ext_list:
            return fmt
    return None


def _health_score(gdf: gpd.GeoDataFrame) -> Usual_Dict:
    # With the assistance of Claude:
    # see: ./docs/gpkg health.md
    """
    A file with no issues scores 100 %.
    A file where every row has an invalid geometry scores close to 0 %
    that component alone drags it to ~64 % if everything else is clean,
    because invalid geom carries 10/28 of the weight.

    All four problems at full severity → 0 %.
    """
    n = len(gdf)

    # Raw counts / flags
    invalid_geom = int((~gdf.is_valid).sum())
    empty_geom = int(gdf.geometry.is_empty.sum())
    missing_crs = int(gdf.crs is None)  # 0 or 1
    null_values = int(gdf.isna().sum().sum())

    # Weights (1–10 scale, higher = more damaging)
    W_INVALID_GEOM = 10  # breaks spatial ops entirely [Breaks sjoin, overlay, buffer — catastrophic]
    W_EMPTY_GEOM = 6  # silent data loss [Data loss; geometry column exists but is useless]
    W_MISSING_CRS = 8  # projections / overlays fail [Silent wrong results on any projection operation]
    W_NULL_VALUES = 4  # attribute gaps, less critical [Attribute gaps; layer still spatially usable]

    TOTAL_WEIGHT = W_INVALID_GEOM + W_EMPTY_GEOM + W_MISSING_CRS + W_NULL_VALUES  # 28

    def _penalty(count: int, weight: int, max_count: int) -> float:
        """Fractional penalty [0.0 – weight] for one issue."""
        if max_count == 0:
            return 0.0
        ratio = min(count / max_count, 1.0)  # cap at 100 %
        return ratio * weight

    penalties = (
        _penalty(invalid_geom, W_INVALID_GEOM, n)
        + _penalty(empty_geom, W_EMPTY_GEOM, n)
        + _penalty(missing_crs, W_MISSING_CRS, 1)  # binary: 0 or 1
        + _penalty(null_values, W_NULL_VALUES, n * len(gdf.columns))
    )

    score = round((1 - penalties / TOTAL_WEIGHT) * 100, 1)

    return {
        "score_pct": score,
        "issues": {
            "invalid_geometries": {"count": invalid_geom, "weight": W_INVALID_GEOM},
            "empty_geometries": {"count": empty_geom, "weight": W_EMPTY_GEOM},
            "missing_crs": {"count": missing_crs, "weight": W_MISSING_CRS},
            "null_values": {"count": null_values, "weight": W_NULL_VALUES},
        },
    }


def _get_spd_info(
    started_at: datetime, gdf: gpd.GeoDataFrame, layers: pd.DataFrame, layer_index: int = 0, values_from_fields: List[str] = []
) -> Usual_Dict:
    """
    Reads a GeoDataFrame, extracts metadata including engine versions, bounding box,
    field list, and column details:
    [data type, non-null count, unique values for specified fields in from_fields:
          from_fields =
            [] : no values
            ['*']:  values of all fields
            ['id', 'name']: values from list's fields
        ]

    Returns a structured dict for further processing.
    """

    def __build_values(hashable_fields: List[str]) -> Tuple[List[str], Usual_Dict]:
        def ___get_values_of(field: str) -> List[Primitive]:
            def ____to_native(value):
                return value.item() if hasattr(value, "item") else value

            return [____to_native(v) for v in gdf[field].dropna().unique()] if all_columns or field in values_from_fields else []

        fields: List[str] = []
        values: Usual_Dict = {}
        all_columns = values_from_fields == SPD_VALUES_FROM_ALL_FIELDS
        for column in gdf.columns:
            col_values = ___get_values_of(column) if column in hashable_fields and (all_columns or column in values_from_fields) else []
            if col_values:
                fields.append(column)
                values[column] = col_values

        return fields, values

    def __hashable_fields() -> List[str]:
        hashable_fields = []
        for column in gdf.columns:
            hashable_fields.append(column)
            for v in gdf[column].dropna().head(10):
                try:
                    hash(v)
                except Exception:
                    hashable_fields.remove(column)
                    break

        return hashable_fields

    spd_data: Usual_Dict = {
        "version": SPD_MODULE_VERSION,
        "created": now_as_iso(),
        "error": "",
    }

    f = ""
    try:
        spd_data[f := "engines"] = {
            "pandas": pd.__version__,
            "pyogrio": pyogrio.__version__,
            "geopandas": gpd.__version__,
        }

        # better way to check layers is valid?
        _layers_name = [] if layers is None else layers["name"].tolist()
        _geoms_type = [] if layers is None else layers["geometry_type"].tolist()
        _crs = gdf.crs.to_string() if gdf.crs else ""

        feature_count = len(gdf)
        valid_features = int(gdf.is_valid.sum())
        valid_pct = 100 * valid_features / feature_count if feature_count > 0 else 0

        # todo: send error in result
        if len(_layers_name) <= layer_index:
            raise Exception("Invalid `layers` or `layer_index` parameters.")
        i = layer_index
        spd_data[f := "layer"] = {"index": i, "name": _layers_name[i], "geom_type": _geoms_type[i], "crs": _crs}
        spd_data[f := "features"] = {"count": feature_count, "valid": valid_features, "valid_pct": valid_pct}
        spd_data[f := "health_score"] = _health_score(gdf)
        spd_data[f := "bounds"] = (gdf.total_bounds.tolist(),)

        hashable_fields = __hashable_fields()
        fields_with_values, values = __build_values(hashable_fields)

        fields: Usual_Dict = {}
        for column in gdf.columns:
            series = gdf[column]
            non_null = series.dropna()
            unique_vals_len = len(non_null.unique()) if column in hashable_fields else -1
            has_values = column in fields_with_values

            fields[column] = {
                "type": str(gdf[column].dtype),
                "hashable": column in hashable_fields,
                "total_count": len(series),
                "non_null_count": len(non_null),
                "unique_count": unique_vals_len,
                "has_values": has_values,
            }

        spd_data[f := "fields"] = fields
        spd_data[f := "values"] = values

    except Exception as e:
        # Note: f might still hold the previous attribute if the failure happens before assignment
        spd_data["error"] = f"Error setting attribute [{f}]: {e}"

    spd_data["elapsed_ms"] = round((datetime.now() - started_at).total_seconds() * 1000)
    return spd_data


def spd_info_from_file(spd_ffname: str, layer_index: int = 0, values_from_fields: List[str] = []) -> Usual_Dict:
    """
    Reads the file (with the specified name `spd_ffname`) and extracts metadata
     of the layer with index `layer_index`, including
    engine versions, bounding box, field list, and column details:
    Reads a GeoDataFrame, extracts metadata including engine versions, bounding box,
    field list, and column details:

    [data type, non-null count, unique values for specified fields in from_fields:
          from_fields =
            [] : no values
            ['*']:  values of all fields
            ['id', 'name']: values from list's fields
        ]

    Returns a structured dict for further processing.    Returns a structured dict for further processing.
    """

    return spd_info_from_bytes(b"", f"{_SPD_FORMAT_FILE}{_SPD_FILE_NAME_SEP}{spd_ffname}", layer_index, values_from_fields)


def spd_info_from_bytes(bytes_data: bytes, format: str, layer_index: int = 0, values_from_fields: List[str] = []) -> Usual_Dict:
    """
    Reads bytes_data is binary as binary geospatial data data (with the specified `format`)
    of the layer with index layer_index
    extracts metadata including: engine versions, bounding box, field list, and column details:
        {'type': data type,
          'qtd': non-null count,
          'values': unique values for the specified fields
          from_fields =
            [] : no values
            ['*']:  values of all fields
            ['id', 'name']: values from list's fields
        ]

    Returns a structured dict for further processing.
    """

    started = datetime.now()
    gpd.options.io_engine = "pyogrio"
    _max = 2
    [drv, file_name, _] = (format + _max * _SPD_FILE_NAME_SEP).split(_SPD_FILE_NAME_SEP, _max)

    # If a file_name:
    if same_entry(drv, _SPD_FORMAT_FILE):
        gdf = gpd.read_file(file_name)
        layers = gpd.list_layers(file_name)
        return _get_spd_info(started, gdf, layers, layer_index, values_from_fields)

    # else From Bytes:
    if same_entry(drv, SPD_FORMAT_SHP):
        _driver = "ESRI Shapefile"
    elif same_entry(format, SPD_FORMAT_GPKG):
        _driver = "GPKG"
    elif same_entry(format, SPD_FORMAT_GEOJSON):
        _driver = "GeoJSON"
    else:  # todo raise error
        return {}

    gdf = gpd.read_file(BytesIO(bytes_data), driver=_driver)

    raw_layers = pyogrio.list_layers(BytesIO(bytes_data))  # CAUTION, not the same 'format' as gpd.list_layers(file_name)
    layers = pd.DataFrame(raw_layers, columns=["name", "geometry_type"])  # make them 'compatible'

    spd_data = _get_spd_info(started, gdf, layers, layer_index, values_from_fields)

    return spd_data


# eof
