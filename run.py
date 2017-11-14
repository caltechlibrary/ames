from harvesters import get_crossref_refs
from harvesters import get_datacite_refs
from matchers import match_cd_refs
import os,subprocess,json
import requests

def send_simple_message(token,matched):
    matched_doi = matched[0]
    matched_key = matched[1]
    os.environ['AWS_SDK_LOAD_CONFIG']="1"
    metadata =\
        subprocess.check_output(["dataset","-c","s3://dataset.library.caltech.edu/CaltechDATA","read",matched_key],universal_newlines=True)
    metadata = json.loads(metadata)['metadata']
    title = metadata['title']
    doi = metadata['doi']
    headers = {'Accept':'text/bibliography; style=american-medical-association'}
    citation  = requests.get(matched_doi,headers=headers)
    citation = citation.text
    email = ''
    name = ''
    for c in metadata['contributors']:
        if c['contributorType']=='ContactPerson':
            email = c['contributorEmail']
            name = c['contributorName']
    if email == '':
        print("No email listed, Nothing sent")
    else:
        return requests.post(
            "https://api.mailgun.net/v3/sandbox70ed6f90214048a1b111544cf8207b77.mailgun.org/messages",
            auth=("api", token),
            files=[("inline", open("CaltechDATA_Logo_cropped.png",'rb'))],
            data={"from": "Mailgun Sandbox <postmaster@sandbox70ed6f90214048a1b111544cf8207b77.mailgun.org>",
              "to": "Tom Morrell <tmorrell@caltech.edu>",
              "subject": "Your CaltechDATA Work has a New Citation!",
              "html": '<html> <center> <img src="cid:CaltechDATA_Logo_cropped.png"\
                      alt="CaltechDATA Logo" width="498" height="139"> </center> \
                      <p> Dear '+name+', </p>\
                      <p>Your CaltechDATA work "'+title+'" has been cited\
                      in:</p><p>'+citation+'</p><p>This\
                      link has been added to your CaltechDATA record at \
                      <a href="https://doi.org/'+doi+'">'+doi+'</a>.</p>\
                      <p> Is this incorrect?  Let us know at\
                      <a href="mailto:data@caltech.edu?Subject=Issue%20with%20citation%20link%20between%20'\
                      +doi+'%20and%20'+matched_doi+'">data@caltech.edu</a></p>\
                      <P> This email was sent by the Caltech Library, \
                      1200 East California Blvd., MC 1-43, Pasadena, CA 91125, USA </p> </html>'})


            #matches = [["https://doi.org/10.3390/rs8050414",'285']]

#"https://caltechdata.tind.io/tindfiles/serve/5df8a197-3fa2-4760-b555-e185d95c52dd/"\
        #                      alt="CaltechDATA Logo" width="400" height="200"> </center> \

get_crossref_refs(False)
matches = match_cd_refs()

token = os.environ['MAILTOK']
for m in matches:
    send_simple_message(token,m)
