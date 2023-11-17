from datetime import datetime

import httpx
import re
from parsel import Selector
from pathlib import Path
from tqdm.auto import tqdm
from loguru import logger
import safer
import typer


def find_and_parse_date(text: str) -> datetime | None:
    # Regular expression for the date pattern "%B_%Y"
    month_year_pattern = (
        r"(January|February|March|April|May|June|July|August|September|October|November|December)_\d{4}"
    )
    match = re.search(month_year_pattern, text)
    if match:
        date_str = match.group()
        date_obj = datetime.strptime(date_str, "%B_%Y")
        return date_obj

    year_pattern = r"_\d{4}"
    match = re.search(year_pattern, text)
    if match:
        date_str = match.group()
        date_obj = datetime.strptime(date_str, "_%Y")
        return date_obj

    return None


def main(
    save_path: Path = Path("./vessel_positions"),
    start_date: datetime = datetime(1998, 1, 1),
    overwrite: bool = False,
):
    start_date = datetime(start_date.year, start_date.month, 1)

    result = httpx.get(
        "https://www.operations.amsa.gov.au/Spatial/DataServices/DigitalData",
        timeout=60.0,
    )

    if result.status_code != 200:
        logger.error("Failed to get vessel position file list")
        exit()

    html_selector = Selector(text=result.text)
    rows = html_selector.css("div.lineitem")

    data_download_ids = [(row.css("strong::text")[0].get(), row.css("button").attrib["onclick"][13:-2]) for row in rows]

    save_path.mkdir(parents=True, exist_ok=True)
    existing_files = list(save_path.glob("*.zip"))

    # Regular expression pattern: transition from letters to numbers
    alpha_to_numeral_transition_regex = r"([a-zA-Z])(\d)"

    for desc, download_id in tqdm(data_download_ids):
        if "sub-areas" in desc or "Vessel Traffic Data" not in desc:
            continue

        # Some AMSA descriptions have inconsistent spacing and periods
        clean_desc: str = desc.strip().replace(" ", "_").replace(".", "")
        clean_desc = re.sub(alpha_to_numeral_transition_regex, r"\1_\2", clean_desc)
        file_name = f"{clean_desc}.zip"
        file_path = save_path / file_name

        if start_date:
            file_date = find_and_parse_date(clean_desc)
            if file_date and file_date < start_date:
                continue

        if not overwrite and file_path in existing_files:
            logger.info(f"File: {file_path} already exists - skipping")
            continue

        response = httpx.post(
            "https://www.operations.amsa.gov.au/Spatial/DataServices/Download",
            data={"ContentItemId": int(download_id), "TermsAccepted": True},
            timeout=300.0,
        )

        if response.status_code == 200:
            file_extension = response.headers["content-type"].split("/")[1]
            if file_extension != "zip":
                logger.error(
                    f"Download for: {desc} had unexpected file content type {response.headers['content-type']}"
                )
                continue
            with safer.open(file_path, "wb") as fp:
                fp.write(response.content)
        else:
            logger.warning(f"Failed to download content for: {desc}")


if __name__ == "__main__":
    typer.run(main)
