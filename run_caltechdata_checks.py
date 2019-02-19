import os,getpass,shutil
from ames.harvesters import get_caltechdata
from ames.matchers import fix_multiple_links
from ames.matchers import update_datacite_metadata

collection = 'caltechdata.ds'
if os.path.isdir('data') == False:
    os.mkdir('data')
os.chdir('data')

shutil.rmtree(collection)

token = os.environ['TINDTOK']

get_caltechdata(collection,datacite=True)
fix_multiple_links(collection,token)
check = input("Do you want to update DOI metadata with DataCite? Y or N:")
if check == 'Y':
    password = getpass.getpass("Enter the TIND DataCite Password:")
    update_datacite_metadata(collection,token,password)
