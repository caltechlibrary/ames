import unittest
import os, copy, time, requests
import pandas as pd
from run_subject_id_correction import all_corrected 
from caltechdata_api import caltechdata_write, get_metadata

os.environ["RDMTOK"] = "FVyjwsxBvfNXm5NmmfL8fKGI8hhA6puT9pNJO8PAyrLlNYdeMjfjhBVvuhbs"

headers = {
    "Authorization": "Bearer %s" % "FVyjwsxBvfNXm5NmmfL8fKGI8hhA6puT9pNJO8PAyrLlNYdeMjfjhBVvuhbs",
    "Content-type": "application/json",
}

original_metadata = {
    "titles": [{"title": "enter title"}],
    "creators": [
        {
            "familyName": "Abakah",
            "givenName": "Alexander",
            "nameType": "Personal",
            "nameIdentifiers": [
                {"nameIdentifier": "0009-0003-5640-6691", "nameIdentifierScheme": "ORCID"}
            ],
            "affiliations": [{"affiliation": "Caltech"}]
        }
    ],
    "types": {"resourceType": "Dataset", "resourceTypeGeneral": "Dataset"},
    "descriptions": [{"description": "A data set of forest fires", "descriptionType": "Summary"}],
    "dates": [{"date": "2023-11-30", "dateType": "Created"}],
    "publisher": "Caltech Library",
    "subjects": [{"subject": "Enter Subject"}],
}

# A version of the metadata that is deliberately malformed
malformed_metadata = copy.deepcopy(original_metadata)
malformed_metadata["subjects"] = [
    {"subject": "  Biological sciences  "},  # Extra spaces
    {"subject": "CHEMICAL SCIENCES"},        # All caps
    {"subject": "computer and information sciences"},  # Incorrect capitalization
]

df = pd.read_csv("subjects_to_correct.csv")

subjects_to_correct = dict(zip(df['subject'], df['subject url']))

def test_change(record_id):
    metadata = get_metadata(record_id, production = False)
    for i in metadata["subjects"]:
        for each_correct_subject in subjects_to_correct.keys():
            if "id" in i.keys():
                if (
                    i["subject"] == each_correct_subject
                    and i["id"] != subjects_to_correct[each_correct_subject]
                ):
                    print(i["subject"], "'s id wasn't added.")
                    return False
    print("Changes made!")
    return True


class TestSubjects(unittest.TestCase):

    def test_subject_changes(self):
        # Creates a test record with malformed subjects
        test_data = copy.deepcopy(malformed_metadata)
        record_id = caltechdata_write(
            metadata=test_data,
            production=False,
            publish=True
        )
        # Verify correction
        self.assertEqual(all_corrected(record_id), True, f"Subjects in record {record_id} were not corrected properly")
        self.assertEqual(test_change(record_id), True)
        print("Passed test_subject_changes")

        #Verify no change was made to original metadata
        record_id = caltechdata_write(
            metadata=copy.deepcopy(original_metadata),
            production=False,
            publish=True
        )
        self.assertEqual(all_corrected(record_id), True, f"Subjects in original record {record_id} were not edited properly")
        self.assertEqual(test_change(record_id), True)
        print("Passed test_subject_changes")

    def test_subject_id_present(self):
        # Creates a record with known subjects that should map to IDs
        test_data = copy.deepcopy(malformed_metadata)
        test_data["subjects"] = [
            {"subject": "Biological sciences"},
            {"subject": "Chemical sciences"},
            {"subject": "Computer and information sciences"},
        ]
        record_id = caltechdata_write(
            metadata=test_data,
            production=False,
            publish=True
        )

        all_corrected(record_id)

        rurl = "https://data.caltechlibrary.dev/api/records/" + record_id
        data = requests.get(rurl, headers=headers).json()
        record_metadata = data["metadata"]
        for subject_obj in record_metadata.get("subjects", []):
            if subject_obj["subject"] in ["Biological sciences", "Chemical sciences", "Computer and information sciences"]:
                self.assertIn("id", subject_obj, f"Subject '{subject_obj['subject']}' in record {record_id} should have an ID")
        print("Passed test_subject_id_present")

    def test_subject_scheme_consistent(self):
        # Creates a record with IDs that should link to scheme FOS
        test_data = copy.deepcopy(original_metadata)
        test_data["subjects"] = [
            {
                "id": "http://www.oecd.org/science/inno/38235147.pdf?1.2",
                "subject": "Computer and information sciences",
                "scheme": "fos"
            }
        ]
        record_id = caltechdata_write(
            metadata=test_data,
            production=False,
            publish=True
        )

        all_corrected(record_id)

        record_metadata = get_metadata(
            record_id, production=False
        )
        for subject_obj in record_metadata.get("subjects", []):
            if "id" in subject_obj:
                self.assertEqual(
                    subject_obj["scheme"], "FOS",
                    f"Subject scheme for '{subject_obj['subject']}' in record {record_id} should be 'FOS'"
                )
        print("Passed test_subject_scheme_consistent")
    
    def test_subject_has_scheme(self):
        # Creates a record with IDs doesn't have a scheme
        test_data = copy.deepcopy(original_metadata)
        test_data["subjects"] = [
            {
                "id": "http://www.oecd.org/science/inno/38235147.pdf?1.2",
                "subject": "Computer and information sciences",
            }
        ]
        record_id = caltechdata_write(
            metadata=test_data,
            production=False,
            publish=True
        )

        all_corrected(record_id)

        record_metadata = get_metadata(
            record_id, production=False
        )
        for subject_obj in record_metadata.get("subjects", []):
            if "id" in subject_obj:
                self.assertIn(
                    "scheme", subject_obj,
                    f"Subject with ID '{subject_obj['id']}' should have a scheme"
                )
        print("Passed test_subject_has_scheme")


if __name__ == '__main__':
    unittest.main()