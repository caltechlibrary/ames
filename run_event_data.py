from ames.harvesters import get_crossref_refs
from ames.harvesters import get_caltechdata
from ames.matchers import match_cd_refs
from xml.sax import saxutils as su
import os
import requests
from py_dataset import dataset

# Environment variable AWS_SDK_LOAD_CONFIG=1 must be set before running


def send_simple_message(token, matched):
    matched_key = matched[0]
    matched_dois = matched[1]
    # Use raw api call to get email
    api_url = "https://data.caltech.edu/api/record/"
    r = requests.get(api_url + matched_key)
    r_data = r.json()
    if "message" in r_data:
        raise AssertionError(
            "id "
            + idv
            + " expected http status 200, got "
            + r_data.status
            + r_data.message
        )
    if not "metadata" in r_data:
        raise AssertionError("expected as metadata property in response, got " + r_data)
    metadata = r_data["metadata"]
    email = ""
    name = ""
    for c in metadata["contributors"]:
        if c["contributorType"] == "ContactPerson":
            if "contributorEmail" in c:
                email = c["contributorEmail"]
                name = c["contributorName"]
            else:
                print("Missing email for record ", matched_key)
    # Use dataset version to get datacite metadata
    metadata, err = dataset.read("caltechdata.ds", matched_key)
    if err != "":
        print(f"Unexpected error on read: {err}")
    title = metadata["titles"][0]["title"]
    doi = metadata["identifier"]["identifier"]
    headers = {"Accept": "text/bibliography;style=apa"}
    citation_block = ""
    for matched in matched_dois:
        citation = requests.get(matched, headers=headers)
        citation.encoding = "utf-8"
        citation = citation.text
        citation = su.unescape(citation)
        citation_block = citation_block + "<p>" + citation + "</p>"
    # Send email
    if email == "":
        print("No email listed, Nothing sent")
    else:
        return requests.post(
            "https://api.mailgun.net/v3/notices.caltechlibrary.org/messages",
            auth=("api", token),
            files=[("inline", open("CaltechDATA_Logo_cropped.png", "rb"))],
            data={
                "from": "CaltechDATA Notices <mail@notices.caltechlibrary.org>",
                "to": name + " <" + email + ">, Tom Morrell <tmorrell@caltech.edu>",
                "subject": "Your CaltechDATA Work has been cited!",
                "html": '<html> <center> <img src="cid:CaltechDATA_Logo_cropped.png"\
                      alt="CaltechDATA Logo" width="249" height="69"> </center> \
                      <p> Dear '
                + name
                + ', </p>\
                      <p>Your CaltechDATA work "'
                + title
                + '" has been cited\
                      in:</p>'
                + citation_block
                + '<p>The\
                      citation(s) are now listed in your CaltechDATA record at \
                      <a href="https://doi.org/'
                + doi
                + '">'
                + doi
                + '</a>.</p>\
                      <p> Best, </p><p>CaltechDATA Alerting Service</p><hr>\
                      <p> Is this incorrect?  Let us know at\
                      <a href="mailto:data@caltech.edu?Subject=Issue%20with%20citation%20link%20between%20'
                + doi
                + "%20and%20"
                + ",".join(matched_dois)
                + '">data@caltech.edu</a></p>\
                      <P> This email was sent by the Caltech Library, \
                      1200 East California Blvd., MC 1-43, Pasadena, CA 91125, USA </p> </html>',
            },
        )


if __name__ == "__main__":
    if os.path.isdir("data") == False:
        os.mkdir("data")
    os.chdir("data")
    get_crossref_refs(False)
    get_caltechdata("caltechdata.ds")
    matches = match_cd_refs()

    for m in matches:
        token = os.environ["MAILTOK"]
        send_simple_message(token, m)
