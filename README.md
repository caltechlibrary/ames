# ames

[![DOI](https://data.caltech.edu/badge/110025475.svg)](https://data.caltech.edu/badge/latestdoi/110025475)

Automated Metadata Service

Manage metadata from different sources.  The examples in the package are
specific to Caltech repositories, but could be generalized.  This package 
is currently in development and will have additional sources and matchers 
added over time.

## Install:

Requires Python 3.7 (Recommended via [Anaconda](https://www.anaconda.com/download))

If you just need functions (like codemeta_to_datacite) type `pip install ames`
If you want to run operations, download the 
[latest release](https://github.com/caltechlibrary/ames/releases), extract the
zip, navigate to the extracted folder and type `python setup.py install`.  

Harvesting requires [Dataset](https://github.com/caltechlibrary/dataset).

CaltechDATA integration requires [caltechdata_api](https://github.com/caltechlibrary/caltechdata_api)

## Organization

### Harvesters

- crossref_refs - Harvest references in datacite metadata from crossref event data
- caltechdata - Harvest metadata from CaltechDATA
- cd_github - Harvest GitHub repos and codemeta files from CaltechDATA
- matomo - Harvest web statistics from matomo
- caltechfeeds - Harvest Caltech Library metadata from feeds.library.caltech.edu

### Matchers

- caltechdata - Match content in CaltechDATA
- update_datacite - Match content in DataCite

## Example Operations

The run scripts show examples of using ames to perform a specific update
operation.

### CodeMeta management

In the test directory these is an example of using the codemeta_to_datacite
function to convert a codemeta file to DataCite standard metdata

### CodeMeta Updating

Collect GitHub records in CaltechDATA, search for a codemeta.json file, and
update CaltechDATA with new metadata.

#### Setup
You need to set an environmental variable with your token to access
CaltechDATA `export TINDTOK=`

#### Usage

Type `python run_codemeta.py`. 

### CaltechDATA Citation Alerts

Harvest citation data from the Crossref Event Data API, records in
CaltechDATA, match records, update metadata in CaltechDATA, and send email to
user.

#### Setup
You need to set environmental variables with your token to access
CaltechDATA `export TINDTOK=` and Mailgun `export MAILTOK=`.

#### Usage

Type `python run_event_data.py`. You'll be prompted for confirmation if any 
new citations are found.  

### Media Updates

Update media records in DataCite that indicate the files associated with a DOI.

#### Setup
You need to set an environmental variable with your password for your DataCite
account using `export DATACITE=`

#### Usage

Type `python run_media_update.py`.  

### CaltechDATA metadata checks

This will run checks on the quality of metadata in CaltechDATA.  Currently this
verifies whether redundent links are present in the related identifier section.  
It also can update metadata with DataCite.

#### Setup
You need to set environmental variables with your token to access
CaltechDATA `export TINDTOK=`

#### Usage

Type `python run_caltechdata_checks.py`. 

### CaltechDATA metadata updates

This will improve the quality of metadata in CaltechDATA.  This option is
broken up into updates that should run frequently (currently every 10 minutes)
and daily. Frequent updates include adding a recommended citation to the
descriptions, and daily updates include adding CaltechTHESIS DOIs to
CaltechDATA.

#### Setup
You need to set environmental variables with your token to access
CaltechDATA `export TINDTOK=`

#### Usage

Type `python run_caltechdata_updates.py` or `python run_caltechdata_daily.py`. 

### Matomo downloads

This will harvest download information from matomo.  Very experimental.  

#### Setup
You need to set environmental variables with your token to access
Matomo `export MATTOK=`

#### Usage

Type `python run_downloads.py`. 

### CODA Reports

Runs reports on Caltech Library repositories.  Current reports:

- doi_report: Records (optionally filtered by year) and their DOIs.
- creator_report: Finds records where an Eprints Creator ID has an ORCID 
but it is not included on all records.  Also lists cases where an author has
two ORCIDS.
- file_report: Records that have potential problems with the attached files
- status_report: Reports on any records with an incorrect status in feeds
- license_report: Report out the license types in CaltechDATA

#### Usage

Type something like `python run_coda_report.py doi_report thesis report.tsv -year 1977-1978`

- The first option is the report type 
- Next is the repository (thesis or authors)
- Next is the output file name (include .csv or .tsv extension, will show up in current directory)

#### Options
- Some reports include a -year option to return just the records from a specific year (1977) or a
range (1977-1978)
- Some reports include a -group option to return just the records with a
  specific group name.  Surround long names with quotes (e.g. "Keck Institute for Space Studies")
- Some reports include a -item option to return just records with a
  specific item type.  Supported types include:
    - CaltechDATA item types (Dataset, Software, ...)
    - CaltechAUTHORS item types (article, monograph, ...)
    - CaltechAUTHORS monograph sub-types
        - discussion_paper
        - documentation
        - manual
        - other
        - project_report
        - report
        - technical_report
        - white_paper
        - working_paper

There are some additional technical arguments if you want to change the default behavior.
- Adding `-source eprints` will pull report data from Eprints instead of feeds.  This is
very slow.  You may need to add -username and -password to provide login
credentials
- Adding `-sample XXX` allows you to select a number of randomly selected records.  This makes it
  more reasonable to pull data directly from Eprints.

You can combine multiple options to build more complex queries, such as this
request for reports from a group:

```
python run_coda_report.py doi_report authors keck_tech_reports.csv -group "Keck Institute for Space Studies" -item technical_report project_report discussion_paper
```

