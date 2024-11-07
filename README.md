# ames

[![DOI](https://img.shields.io/badge/dynamic/json.svg?label=DOI&query=$.pids.doi.identifier&uri=https://data.caltech.edu/api/records/5nghh-75k34/versions/latest)](https://data.caltech.edu/records/5nghh-75k34/latest)

Automated Metadata Service

Manage metadata from different sources.  The examples in the package are
specific to Caltech repositories, but could be generalized.  This package
is currently in development and will have additional sources and matchers
added over time.

## Install

You need to have Python 3.7 or later on your machine.

If you just need the python functions to write your own code
(like codemeta_to_datacite) open a terminal and type `pip install ames`

## Full Install

The full install will include all the example scripts. You need to have Python 3.7 or later on your machine and git.

### Clone ames

A full install starts by downloading this software using git.  Find where you
want the ames folder to live on your computer in File Explorer or Finder
(This could be the Desktop or Documents folder, for example).  Type `cd `
in anaconda prompt or terminal and drag the location from the file browser into
the terminal window.  The path to the location
will show up, so your terminal will show a command like
`cd /Users/tmorrell/Desktop`.  Hit enter.  Then type
`git clone https://github.com/caltechlibrary/ames.git`. Once you
hit enter you'll see an ames folder.  Type `cd ames`

### Install

Now that you're in the ames folder, type `python setup.py install`.  You can
now run all the different operations described below.

### Updating

When there is a new version of the software, go to the ames
folder in anaconda prompt or terminal and type `git pull`.  You shouldn't need to re-do
the installation steps unless there are major updates.

## Organization

### Harvesters

-   crossref_refs - Harvest references in datacite metadata from crossref event data
-   caltechdata - Harvest metadata from CaltechDATA
-   cd_github - Harvest GitHub repos and codemeta files from CaltechDATA
-   matomo - Harvest web statistics from matomo
-   caltechfeeds - Harvest Caltech Library metadata from feeds.library.caltech.edu

### Matchers

-   caltechdata - Match content in CaltechDATA
-   update_datacite - Match content in DataCite

## Example Operations

The run scripts show examples of using ames to perform a specific update
operation.

### CodeMeta management

In the test directory these is an example of using the codemeta_to_datacite
function to convert a codemeta file to DataCite standard metdata

### CodeMeta Updating

Collect GitHub records in CaltechDATA, search for a codemeta.json file, and
update CaltechDATA with new metadata.

#### CodeMeta Setup
You need to set an environmental variable with your token to access
CaltechDATA `export TINDTOK=`

#### CodeMeta Usage

Type `python run_codemeta.py`.

### CaltechDATA Citation Alerts

Harvest citation data from the Crossref Event Data API, records in
CaltechDATA, match records, update metadata in CaltechDATA, and send email to
user.

#### Citation Alerts Setup
You need to set environmental variables with your token to access
CaltechDATA `export TINDTOK=` and Mailgun `export MAILTOK=`.

#### Citation Alerts Usage

Type `python run_event_data.py`. You'll be prompted for confirmation if any
new citations are found.  

### Media Updates

Update media records in DataCite that indicate the files associated with a DOI.

#### Media Setup
You need to set an environmental variable with your password for your DataCite
account using `export DATACITE=`

#### Media Usage

Type `python run_media_update.py`.  

### CaltechDATA metadata checks

This will run checks on the quality of metadata in CaltechDATA.  Currently this
verifies whether redundent links are present in the related identifier section.  
It also can update metadata with DataCite.

#### Metadata Checks Setup
You need to set environmental variables with your token to access
CaltechDATA `export TINDTOK=`

#### Metadata Checks Usage

Type `python run_caltechdata_checks.py`.

### CaltechDATA Metadata Updates

This will improve the quality of metadata in CaltechDATA.  This option is
broken up into updates that should run frequently (currently every 10 minutes)
and daily. Frequent updates include adding a recommended citation to the
descriptions, and daily updates include adding CaltechTHESIS DOIs to
CaltechDATA.

#### Metadata Updates Setup
You need to set environmental variables with your token to access
CaltechDATA `export TINDTOK=`

#### Metadata Updates Usage

Type `python run_caltechdata_updates.py` or `python run_caltechdata_daily.py`.

### CaltechDATA COUNTER Usage Reports

This will harvest download and view information from matomo and format it into
a COUNTER report.  This feature is still being tested.  

#### Usage Report Setup
You need to set environmental variables with your token to access
Matomo `export MATTOK=`

#### Usage Report Usage

Type `python run_usage.py`.

### Archives Reports

Runs reports on ArchivesSpace.  Current reports:

-   accession_report: Returns accession records that match a certain subject
-   format_report: Returns large report on accessions with certain media formats

Example usage:

python run_archives_report.py accession_report accession.csv -subject "Manuscript Collection"

### Update Eprints

Perform update options using the Eprints API. Supports url updates to https for
resolver field, special character updates, and adjusting the item modified date
(which also regenerates the public view of the page).

Example usage:

python run_eprints_updates.py update_date authors -recid 83420 -user tmorrell -password 

### CODA Reports

Runs reports on Caltech Library repositories.  Current reports:

-   doi_report: Records (optionally filtered by year) and their DOIs.

-   thesis_report: Matches Eprints tsv export for CaltechTHESIS

-   thesis_metadata: Matches Eprints metadata tsv export for CaltechTHESIS

-   creator_report: Finds records where an Eprints Creator ID has an ORCID
but it is not included on all records.  Also lists cases where an author has
two ORCIDS.

-   creator_search: Export a google sheet with the author lists of all
    publications associated with an author id. Requires -creator argument

-   people_search: Search across the CaltechPEOPLE collection by division

-   file_report: Records that have potential problems with the attached files

-   status_report: Reports on any records with an incorrect status in feeds

-   record_number_report: Reports on records where the record number and resolver
URL don't match

-   alt_url_report: Reports on records with discontinure alt_url field

-   license_report: Report out the license types in CaltechDATA

#### Report Usage

Type something like `python run_coda_report.py doi_report thesis report.tsv -year 1977-1978`

-   The first option is the report type
-   Next is the repository (thesis or authors)
-   Next is the output file name (include .csv or .tsv extension, will show up in current directory)

#### Report Options

-   Some reports include a -year option to return just the records from a specific year (1977) or a
range (1977-1978)

-   Some reports include a -group option to return just the records with a
specific group name.  Surround long names with quotes (e.g. "Keck Institute for Space Studies")

-   Some reports include a -item option to return just records with a
specific item type.  Supported types include:
    -   CaltechDATA item types (Dataset, Software, ...)
    -   CaltechAUTHORS item types (article, monograph, ...)
    -   CaltechAUTHORS monograph sub-types
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

-   Adding `-source eprints` will pull report data from Eprints instead of feeds.  This is
very slow.  You may need to add -username and -password to provide login
credentials

-   Adding `-sample XXX` allows you to select a number of randomly selected records.  This makes it
  more reasonable to pull data directly from Eprints.

You can combine multiple options to build more complex queries, such as this
request for reports from a group:

```console
python run_coda_report.py doi_report authors keck_tech_reports.csv -group "Keck Institute for Space Studies" -item technical_report project_report discussion_paper
```

```console
python run_coda_report.py people_search people chem.csv -search "Chemistry and Chemical Engineering Division"
```
