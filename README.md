# ames

[![DOI](https://data.caltech.edu/badge/110025475.svg)](https://data.caltech.edu/badge/latestdoi/110025475)

Automated Metadata Service

This package will update the metadata in our repositories from external sources.  This package is currently in development and will have additional sources and matchers added over time.

Requires: 

Python 3 (Recommended via [Anaconda](https://www.anaconda.com/download)) with reqests library and [Dataset](https://github.com/caltechlibrary/dataset).

CaltechDATA integration requires [caltechdata_api](https://github.com/caltechlibrary/caltechdata_api)

## Harvesters

- datacite_refs - Harvest references in datacite metadata from crossref event data
- crossref_refs - Harvest references in datacite metadata from crossref event data
- cd_github - Harvest GitHub repos from CaltechDATA

## Matchers

- caltechdata - Match content in CaltechDATA

## CodeMeta Updating

#### Setup
You need to set an environmental variable with your token to access
CaltechDATA `export TINDTOK=`

#### Usage
Type `python run_codemeta.py`. This will harvest all the repos present in
CaltechDATA, search them for codemeta.json files, and update the metadata
in CaltechDATA. There are more fields that could be mapped in the future.

## CaltechDATA Citation Alerts

#### Setup
You need to set environmental variables with your token to access
CaltechDATA `export TINDTOK=` and Mailgun `export MAILTOK=`.  Access to data on S3 is currently
restricted to Caltech Library staff and your S3 configuration needs to be set up
following the instructions in Dataset.

#### Usage
Type `python run_event_data.py`. You will automatically generate citation alerts for all DOIs in the CaltechDATA repository.  
This script collects citation data from the Crossref Event Data API, matches DOIs with those 
in CaltechDATA, updates the metadata in CaltechDATA, and sends an email alert to the contact 
person for the data record. You'll be prompted if any citations are found.  
