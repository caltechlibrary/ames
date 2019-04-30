import requests
from py_dataset import dataset
import os, csv
from ames.harvesters import file_mapping, get_usage
from ames.harvesters import get_caltechdata

if os.path.isdir('data') == False:
    os.mkdir('data')
os.chdir('data')

production = True
collection = 'caltechdata.ds'

get_caltechdata(collection,production)

mapping_file = 'tindfile_mapping.csv'

mapping = file_mapping(collection,mapping_file)

usage_collection = 'usage.ds'

token = os.environ['MATTOK']

get_usage(collection,usage_collection,mapping,token)
