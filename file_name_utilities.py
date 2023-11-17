import re
from datetime import datetime


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
