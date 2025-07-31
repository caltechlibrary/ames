from caltechdata_api import get_metadata
from ames.matchers import edit_subject
import os
import pandas as pd

df = pd.read_csv("subjects_to_correct.csv")

subjects_to_correct = dict(zip(df["subject"], df["subject url"]))


def all_corrected(record, subjects_to_correct=subjects_to_correct):

    metadata = edit_subject(
        record, os.environ.get("CALTECH_DATA_API"), subjects_to_correct
    )

    if metadata:
        return True
    else:
        return False
