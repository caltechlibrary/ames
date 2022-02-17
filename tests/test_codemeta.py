import json
from datacite import schema40
from ames import codemeta_to_datacite

infile = open("codemeta.json", "r")
meta = json.load(infile)
standardized = codemeta_to_datacite(meta)
standardized["identifier"] = {"identifier": "10.1/1", "identifierType": "DOI"}
standardized["titles"] = [{"title": "Title"}]
standardized["publisher"] = "publisher"
standardized["publicationYear"] = "2018"
standardized["resourceType"] = {"resourceTypeGeneral": "Software"}
result = schema40.validate(standardized)
# Debugging if this fails
if result == False:
    v = schema40.validator.validate(standardized)
    errors = sorted(v.iter_errors(instance), key=lambda e: e.path)
    for error in errors:
        print(error.message)
    exit()
else:
    print("Valid DataCite Metadata")
