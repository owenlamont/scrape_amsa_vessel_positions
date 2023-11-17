from datetime import datetime
from pathlib import Path
import zipfile
from io import BytesIO
import tempfile
import geopandas as gpd
import pandas as pd
from tqdm.auto import tqdm
from file_name_utilities import find_and_parse_date
from loguru import logger
import typer


def main(
    read_path: Path = Path("./vessel_positions"),
    write_path: Path = Path("./vessel_position_parquets"),
    start_date: datetime = datetime(1998, 1, 1),
    overwrite: bool = False,
):
    write_path.mkdir(parents=True, exist_ok=True)
    existing_parquets = list(write_path.glob("*.parquet"))
    start_date = datetime(start_date.year, start_date.month, 1)
    file_paths = []
    for file_path in read_path.glob("*.zip"):
        write_file_path = write_path / f"{file_path.stem}.parquet"
        file_date = find_and_parse_date(str(file_path))
        if (file_date is None or file_date >= start_date) and (overwrite or write_file_path not in existing_parquets):
            file_paths.append(file_path)

    for file_path in tqdm(file_paths):
        with zipfile.ZipFile(file_path, "r") as outer_zip:
            for inner_file_name in outer_zip.namelist():
                if inner_file_name.endswith(".zip"):
                    with outer_zip.open(inner_file_name) as inner_zip_file:
                        inner_zip_bytes = BytesIO(inner_zip_file.read())
                        with zipfile.ZipFile(inner_zip_bytes) as inner_zip:
                            with tempfile.TemporaryDirectory() as temp_dir:
                                inner_zip.extractall(path=temp_dir)
                                temp_dir_path = Path(temp_dir)
                                for shapefile_path in temp_dir_path.glob("*.shp"):
                                    gdf = gpd.read_file(str(shapefile_path))
                                    gdf = gdf.rename(
                                        columns={
                                            "DRAFT_MAX": "DRAUGHT",
                                            "TMESTAMP": "TIMESTAMP",
                                            "TIMETAMP": "TIMESTAMP",
                                        }
                                    )
                                    if "DRAFT_MIN" in gdf.columns:
                                        gdf = gdf.drop(columns=["DRAFT_MIN"])
                                    gdf = gdf[
                                        [
                                            "CRAFT_ID",
                                            "LON",
                                            "LAT",
                                            "COURSE",
                                            "SPEED",
                                            "TYPE",
                                            "SUBTYPE",
                                            "LENGTH",
                                            "BEAM",
                                            "DRAUGHT",
                                            "TIMESTAMP",
                                            "geometry",
                                        ]
                                    ].copy()
                                    gdf["SUBTYPE"] = gdf["SUBTYPE"].astype(str)
                                    gdf["TYPE"] = gdf["TYPE"].astype(str)
                                    gdf["TIMESTAMP"] = pd.to_datetime(gdf["TIMESTAMP"], dayfirst=True, format="mixed")
                                    gdf.to_parquet(write_path / f"{file_path.stem}.parquet")


if __name__ == "__main__":
    typer.run(main)
