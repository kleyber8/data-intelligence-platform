import logging
import polars as pl
from curl_cffi import requests
from src.storage.db import get_engine

logger = logging.getLogger("ingestion.ports")
logging.basicConfig(level=logging.INFO)

BASE_API_URL = (
    "https://services9.arcgis.com/j1CY4yzWfwptbTWN/arcgis/rest/services/"
    "WorldPortIndex_WFL1/FeatureServer/0/query"
)

def run():
    logger.info("Consultando la API REST oficial del World Port Index (NGA)...")
    
    all_features = []
    offset = 0
    batch_size = 1000

    while True:
        params = {
            "where": "1=1",
            "outFields": "*",
            "f": "json",
            "resultOffset": offset,
            "resultRecordCount": batch_size,
        }

        resp = requests.get(BASE_API_URL, params=params, impersonate="chrome110", timeout=60)
        resp.raise_for_status()
        data = resp.json()
        
        features = data.get("features", [])
        if not features:
            break

        all_features.extend(features)
        logger.info(f"  → Obtenidos {len(features)} puertos (Total: {len(all_features)})")

        if len(features) < batch_size:
            break
        offset += batch_size

    logger.info(f"Total de puertos descargados: {len(all_features)}")

    # El formato de ArcGIS usa 'attributes' para los campos y 'geometry' con x/y
    records = []
    for feature in all_features:
        attrs = feature.get("attributes", {})
        geom = feature.get("geometry", {})

        # Intentamos obtener las coordenadas de geometry (x,y) o de attributes
        lat = geom.get("y") or attrs.get("LATITUDE") or attrs.get("latitude")
        lon = geom.get("x") or attrs.get("LONGITUDE") or attrs.get("longitude")

        if lat is None or lon is None:
            continue

        records.append({
            "port_index": str(attrs.get("INDEX_NO", attrs.get("index_no", ""))),
            "region_name": str(attrs.get("REGION_NO", attrs.get("region_no", ""))),
            "port_name": str(attrs.get("PORT_NAME", attrs.get("port_name", ""))),
            "country": str(attrs.get("COUNTRY", attrs.get("country", ""))),
            "latitude": float(lat),
            "longitude": float(lon),
            "harbor_size": str(attrs.get("HARBORSIZE", attrs.get("harbor_size", ""))),
            "harbor_type": str(attrs.get("HARBORTYPE", attrs.get("harbor_type", ""))),
        })

    if not records:
        logger.error("No se pudieron extraer coordenadas válidas.")
        return

    df = pl.DataFrame(records).drop_nulls(subset=["latitude", "longitude"]).unique(subset=["port_index"])
    logger.info(f"Se procesaron {len(df)} puertos válidos con coordenadas.")

    # Carga a PostgreSQL
    df.write_database(
        table_name="bronze.bronze_ports",
        connection=get_engine(),
        if_table_exists="replace"
    )
    logger.info("✅ Carga en bronze.bronze_ports completada con datos de la API oficial.")

if __name__ == "__main__":
    run()
