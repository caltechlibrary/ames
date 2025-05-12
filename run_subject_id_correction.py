from caltechdata_api import get_metadata
from ames.matchers import edit_subject
import os


def all_corrected():


 record = "2d2wf-j0256"
 subjects_to_correct = {'Biological sciences': 'http://www.oecd.org/science/inno/38235147.pdf?1.6', 'Chemical sciences': 'http://www.oecd.org/science/inno/38235147.pdf?1.4', 'Computer and information sciences': 'http://www.oecd.org/science/inno/38235147.pdf?1.2'}


 metadata = edit_subject("2d2wf-j0256", os.environ.get("CALTECH_DATA_API"), subjects_to_correct)




 for i in metadata["subjects"]:
       for each_correct_subject in subjects_to_correct.keys():
         if "id" in i.keys():
           if i["subject"] == each_correct_subject and i["id"] != subjects_to_correct[each_correct_subject]:
               print(i["subject"],"'s id wasn't added.")
               return False
 print("All subject ids were added")
 return True


all_corrected()

