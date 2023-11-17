# Scrape AMSA Vessel Positions

This repo includes some scripts for downloading and reshaping Australian Maritime Safety Authority (AMSA) vessel tracking data from their [digital data website](https://www.operations.amsa.gov.au/Spatial/DataServices/DigitalData)

## Motivation

AMSA provides a long history of maritime vessel positions around Australia but their digital data site and formats are quite painful to use (a terms of use has to be accepted for each file to download and the vessel data is stored inside double-zipped Shape files).

This repo provides two scripts:

1. scrape_vessel_pos.py to bulk download the full history of vessel position data
2. extract_vessel_pos.py to iterate the double-nested zipped shape files and transform each into geoparquet file
