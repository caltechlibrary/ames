import unittest
import os, copy, time, requests
from run_subject_id_correction import all_corrected 
from caltechdata_api import caltechdata_write, get_metadata

os.environ["RDMTOK"] = "FVyjwsxBvfNXm5NmmfL8fKGI8hhA6puT9pNJO8PAyrLlNYdeMjfjhBVvuhbs"

headers = {
    "Authorization": "Bearer %s" % "FVyjwsxBvfNXm5NmmfL8fKGI8hhA6puT9pNJO8PAyrLlNYdeMjfjhBVvuhbs",
    "Content-type": "application/json",
}

metadata = {
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
malformed_metadata = copy.deepcopy(metadata)
malformed_metadata["subjects"] = [
    {"subject": "  Biological sciences  "},  # Extra spaces
    {"subject": "CHEMICAL SCIENCES"},        # All caps
    {"subject": "computer and information sciences"},  # Incorrect capitalization
]


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
        print("Passed test_subject_changes")

    def test_subject_case_normalization(self):
        # Creates a record whose subjects need case normalization
        test_data = copy.deepcopy(malformed_metadata)
        record_id = caltechdata_write(
            metadata=test_data,
            production=False,
            publish=True
        )
        record_metadata = get_metadata(
            record_id, production=False, validate=True, emails=False, schema="43", token=False, authors=False
        )
        for subject_obj in record_metadata.get("subjects", []):
            if "subject" in subject_obj and isinstance(subject_obj["subject"], str):
                self.assertTrue(
                    subject_obj["subject"][0].isupper(),
                    f"Subject '{subject_obj['subject']}' in record {record_id} should start with uppercase"
                )
        print("Passed test_subject_case_normalization")

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
        time.sleep(5)
        rurl = "https://data.caltechlibrary.dev/api/records/" + record_id
        data = requests.get(rurl, headers=headers).json()
        record_metadata = data["metadata"]
        for subject_obj in record_metadata.get("subjects", []):
            if subject_obj["subject"] in ["Biological sciences", "Chemical sciences", "Computer and information sciences"]:
                self.assertIn("id", subject_obj, f"Subject '{subject_obj['subject']}' in record {record_id} should have an ID")
        print("Passed test_subject_id_present")

    def test_subject_scheme_consistent(self):
        # Creates a record with IDs that should link to scheme FOS
        test_data = copy.deepcopy(metadata)
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
        record_metadata = get_metadata(
            record_id, production=False, validate=True, emails=False, schema="43", token=False, authors=False
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
        test_data = copy.deepcopy(metadata)
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
        record_metadata = get_metadata(
            record_id, production=False, validate=True, emails=False, schema="43", token=False, authors=False
        )
        for subject_obj in record_metadata.get("subjects", []):
            if "id" in subject_obj:
                self.assertIn(
                    "scheme", subject_obj,
                    f"Subject with ID '{subject_obj['id']}' should have a scheme"
                )
        print("Passed test_subject_has_scheme")

    def test_duplicate_subjects_removed(self):
        # Create a record with duplicate subjects
        test_data = copy.deepcopy(metadata)
        test_data["subjects"] = [
            {"subject": "Biological sciences"},
            {"subject": "biological Sciences"},
        ]
        record_id = caltechdata_write(
            metadata=test_data,
            production=False,
            publish=True
        )
        record_metadata = get_metadata(
            record_id, production=False, validate=True, emails=False, schema="43", token=False, authors=False
        )
        subjects_list = [s["subject"].lower() for s in record_metadata.get("subjects", [])]
        self.assertEqual(
            len(subjects_list),
            len(set(subjects_list)),
            f"Found duplicate subjects in record {record_id}"
        )
        print("Passed test_duplicate_subjects_removed")



if __name__ == '__main__':
    unittest.main()