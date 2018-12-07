import os
from ames.harvesters import get_caltechfeed

if os.path.isdir('data') == False:
    os.mkdir('data')
os.chdir('data')

get_caltechfeed('thesis')

