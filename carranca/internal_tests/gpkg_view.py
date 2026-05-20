"""
GPKG file information retriever  —  Canoa


Equipe da Canoa -- 2026
mgd 2026-04-12
"""

# cSpell:words geopandas, municipios gpkg

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import pandas as pd

from carranca.private.spd_analysis import spd_info_from_file

print("-------- IMPORT INFO ---------")
print("pandas:", pd.__version__)

import geopandas as gpd

print("geopandas:", gpd.__version__)

print("Configured engine:", gpd.options.io_engine or "auto")

print("-------- END IMPORT INFO ---------")


def print_info_of(file_name: str):

    gdf = gpd.read_file(file_name, layer=0)  # or layer=0 for first | "layer_name"
    print("--- info")
    print(gdf.info())
    print("--- head")
    print(gdf.head())
    print("--- crs")
    print(gdf.crs)
    print("--- columns")
    print(gdf.columns)
    print("--- dtypes")
    print(gdf.dtypes)
    print("--- geometry.type.value_counts")
    print(gdf.geometry.type.value_counts())
    print("--- gdf.total_bounds")
    print(gdf.total_bounds)  # bbox


if __name__ == "__main__":
    file_name = "D:/Projects/AdaptaBrasil/Recortes/municipios-mauro.gpkg"
    spd_data = spd_info_from_file(file_name, 0, ["*"])
    print(spd_data)
    # print_info_of(file_name)

# eof
