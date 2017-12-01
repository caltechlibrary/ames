# ames

[![DOI](https://data.caltech.edu/badge/110025475.svg)](https://data.caltech.edu/badge/latestdoi/110025475)

Automated Metadata Service

In development- Basic citation alerter implemented. 

Requires: 

Python 3 (Recommended via [Anaconda](https://www.anaconda.com/download)) with reqests library and [Dataset](https://github.com/caltechlibrary/dataset).

CaltechDATA integration requires [caltechdata_api](https://github.com/caltechlibrary/caltechdata_api)

## Harvesters

- datacite_refs - Harvest references in datacite metadata from crossref event data
- crossref_refs - Harvest references in datacite metadata from crossref event data

## Matchers

- caltechdata - Match content in CaltechDATA

## Examples

Collect citation event data, match with CaltechDATA, send email alerts:
'python run.py'

## Setup 
You need to set your environmental variables with your token to access
CaltechDATA (TINDTOK) and Mailgun (MAILTOK).  Access to data on S3 is
restricted to Caltech Library staff and S3 configuration needs to be set up
following the dataset instructions. 

