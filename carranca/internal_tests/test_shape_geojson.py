"""
test_shape_to_geojson.py  —  Canoa
Converts a Shapefile (.shp/.dbf/.shx/.prj) to GeoJSON (EPSG:4326).


Equipe da Canoa -- 2026 + Anthropic Claude
mgd 2026-03-24

Usage
-----
    python test_shape_to_geojson.py municipios.shp
    python test_shape_to_geojson.py municipios.shp -o output/municipios.geojson
    python test_shape_to_geojson.py municipios.shp --indent 0       # minified
    python test_shape_to_geojson.py municipios.shp --encoding utf-8
    python test_shape_to_geojson.py municipios.shp --info            # inspect only, no output

Requirements
------------
    pip install geopandas pyogrio
"""

# cSpell:words  municipios pyogrio Indentação

import sys
import argparse
from pathlib import Path


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="test_shape_to_geojson",
        description="Converte Shapefile → GeoJSON (EPSG:4326)  [Canoa]",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Exemplos:\n"
            "  python test_shape_to_geojson.py municipios.shp\n"
            "  python test_shape_to_geojson.py municipios.shp -o data/municipios.geojson\n"
            "  python test_shape_to_geojson.py municipios.shp --indent 0\n"
            "  python test_shape_to_geojson.py municipios.shp --info\n"
        ),
    )
    p.add_argument(
        "shapefile",
        metavar="ARQUIVO.shp",
        help="Caminho para o arquivo .shp",
    )
    p.add_argument(
        "-o",
        "--output",
        metavar="SAÍDA.geojson",
        default=None,
        help="Arquivo de saída (padrão: mesmo nome do .shp, extensão .geojson)",
    )
    p.add_argument(
        "--indent",
        metavar="N",
        type=int,
        default=0,
        help="Indentação do JSON (0 = minificado, padrão: 2)",
    )
    p.add_argument(
        "--encoding",
        metavar="ENC",
        default="utf-8",
        help="Encoding do .dbf (padrão: utf-8; tente latin-1 ou cp1252 se houver erro)",
    )
    p.add_argument(
        "--info",
        action="store_true",
        help="Apenas inspeciona o arquivo, sem gerar GeoJSON",
    )
    p.add_argument(
        "--redo_shx",
        action="store_true",
        help="Tenta restaurar o arquivo de índice (.shx) se estiver faltando (SHAPE_RESTORE_SHX=YES)",
    )
    return p.parse_args()


# ── Dependency check ──────────────────────────────────────────────────────────
def build_output_path(shp_path: Path, output_arg: str | None) -> Path:
    if output_arg:
        out = Path(output_arg)
    else:
        out = shp_path.with_suffix(".geojson")
    out.parent.mkdir(parents=True, exist_ok=True)
    return out


def main() -> None:
    args = parse_args()
    shp_path = Path(args.shapefile)

    if not shp_path.exists():
        print(f"[erro]  Arquivo não encontrado: {shp_path}", file=sys.stderr)
        sys.exit(1)

    if shp_path.suffix.lower() != ".shp":
        print(f"[aviso] Extensão inesperada '{shp_path.suffix}' — continuando mesmo assim.")

    out_path = build_output_path(shp_path, args.output)

    try:
        from ..private.shape_to_geojson import convert

        info = convert(
            shp_path=shp_path,
            out_path=out_path,
            indent=args.indent,
            encoding=args.encoding,
            info_only=args.info,
            redo_shx=args.redo_shx,
        )
        print(info)
    except Exception as exc:
        print(f"\n[erro]  {exc}", file=sys.stderr)
        print("\nDica: se o erro for de encoding, tente:  --encoding latin-1", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
