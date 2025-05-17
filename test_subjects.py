import unittest
import random, os, copy, time, requests
from run_subject_id_correction import all_corrected 
from caltechdata_api import caltechdata_write, get_metadata

os.environ["RDMTOK"] = "FVyjwsxBvfNXm5NmmfL8fKGI8hhA6puT9pNJO8PAyrLlNYdeMjfjhBVvuhbs"

headers = {
    "Authorization": "Bearer %s" % "FVyjwsxBvfNXm5NmmfL8fKGI8hhA6puT9pNJO8PAyrLlNYdeMjfjhBVvuhbs",
    "Content-type": "application/json",
}


titles = [
    "ClimateData2024",
    "OceanSalinityRecords",
    "GlobalTemperatureSet",
    "PlantGrowthStudy",
    "SoilCompositionData",
    "WildlifeObservation2023",
    "AirQualityMetrics",
    "RainfallPatterns",
    "ForestCoverAnalysis",
    "BirdMigrationData"
]


subjects = [
    {"subject": "Biological Sciences"},
    {"subject": "Econs"},
    {
        "subject": "Mathematics",
    },
    {"subject": "biological Sciences"},
    {
        "id": "http://www.oecd.org/science/inno/38235147.pdf?1.6",
        "subject": "Biological sciences",
        "scheme": "FOS"
    },
    {
        "subject": "Sociology",
    },
    {"subject": "Political Science"},
    {
        "subject": "Medical Sciences",
    },
    {"subject": "Art History"},
    {"subject": "Chemical Sciences"},
    {
        "subject": "Psychology",
    },
    {"subject": "Law"},
    {
        "subject": "Agricultural Sciences",
    },
    {"subject": "Engineering"},
    {
        "id": "http://www.oecd.org/science/inno/38235147.pdf?1.4",
        "subject": "Chemical sciences",
        "scheme": "FOS"
    },
    {"subject": "Computer and information sciences"},
    {
        "subject": "Educational Sciences",
    },
    {"subject": "Linguistics"},
    {"subject": "Religious Studies"},
    {
        "id": "http://www.oecd.org/science/inno/38235147.pdf?1.2",
        "subject": "Computer and information sciences",
        "scheme": "FOS"
    }
]


record_ids = []

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
        },

    ],
    "types": {"resourceType": "Dataset", "resourceTypeGeneral": "Dataset"},
    "descriptions": [{"description": "A data set of forest fires", "descriptionType": "Summary"}],
    "dates": [{"date": "2023-11-30", "dateType": "Created"}],
    "publisher": "Caltech Library",
    "subjects": [{"subject":"Enter Subject"}],
}


# Creating a record with malformed subjects and check correction
malformed_metadata = copy.deepcopy(metadata)
malformed_metadata['subjects'] = [
    {"subject": "  Biological sciences  "}, # Extra spaces
    {"subject": "CHEMICAL SCIENCES"}, # All caps
    {"subject": "computer and information sciences"}, # Incorrect capitalization
]

# Creating a test record
response = caltechdata_write(
    metadata=malformed_metadata,
    production=False,
    publish=True
)
record_ids.append("" + response)


for title_idx in range(len(titles)):
    metadata["titles"][0]["title"] = titles[title_idx]

    number_of_subjects = random.randint(1, len(subjects))


    for subject in range(number_of_subjects):
        subject_index = random.randint(1, len(subjects) - 1)
        if len(metadata["subjects"]) == 1:
            metadata["subjects"][0] = subjects[subject_index]
        else:
            metadata["subjects"].append(subjects[subject_index])

    response = caltechdata_write(
    metadata = metadata,
    production=False,
    publish= True
)


    record_ids.append("" + response)




class TestSubjects(unittest.TestCase):
    
    def setUp(self):
        # Initialize test data
        self.record_ids = record_ids
        
    def test_asubject_changes(self):
        for i in range(len(self.record_ids)):
            self.assertEqual(all_corrected(self.record_ids[i]), True)
        
    
    def test_bsubject_case_normalization(self):
        # Test that subjects with different case get normalized
        for record_id in self.record_ids:
            record_metadata = get_metadata(
                                    record_id,
                                    production=False,
                                    validate=True,
                                    emails=False,
                                    schema="43",
                                    token=False,
                                    authors=False,
    )
            for subject_idx in range(len(record_metadata["subjects"])):
                if "subject" in record_metadata["subjects"][subject_idx] and isinstance(record_metadata["subjects"][subject_idx]["subject"], str):
                    # Check that subjects are properly cased (first letter capitalized)
                    self.assertTrue(record_metadata["subjects"][subject_idx]["subject"][0].isupper(), 
                                   f"Subject '{record_metadata["subjects"][subject_idx]["subject"]}' in record' {record_id} 'should start with uppercase")
    
    def test_csubject_id_present(self):
        time.sleep(5)
        # Test that subjects have proper IDs where applicable
        for record_id in self.record_ids:
            rurl = "https://data.caltechlibrary.dev/api/records/" + record_id
            data = requests.get(rurl, headers=headers).json()
            record_metadata = data["metadata"]
            for subject_idx in range(len(record_metadata["subjects"])):
                if record_metadata["subjects"][subject_idx]["subject"] in ["Biological sciences", "Chemical sciences", 
                                             "Computer and information sciences"]:
                    self.assertIn("id", record_metadata["subjects"][subject_idx], f"Subject '{record_metadata["subjects"][subject_idx]["subject"]}' in record' {record_id} 'should have an ID")
    
    def test_dsubject_scheme_consistent(self):
        # Test that subjects with IDs have consistent schemes
        for record_id in self.record_ids:
            record_metadata = get_metadata(
                                    record_id,
                                    production=False,
                                    validate=True,
                                    emails=False,
                                    schema="43",
                                    token=False,
                                    authors=False,
    )
            for subject_idx in range(len(record_metadata["subjects"])):
                if 'id' in record_metadata["subjects"][subject_idx]:
                    self.assertIn('scheme', record_metadata["subjects"][subject_idx], 
                                 f"Subject with ID '{record_metadata["subjects"][subject_idx]["id"]}' should have a scheme")
                    self.assertEqual(record_metadata["subjects"][subject_idx]["scheme"], 'FOS', 
                                   f"Subject scheme for' {record_metadata["subjects"][subject_idx]["subject"]}'in record' {record_id}' should be 'FOS' but was '{record_metadata["subjects"][subject_idx]["scheme"]}'")
    
    def test_eduplicate_subjects_removed(self):
        # Test that duplicate subjects are removed
        for record_id in self.record_ids:
            record_metadata = get_metadata(
                                    record_id,
                                    production=False,
                                    validate=True,
                                    emails=False,
                                    schema="43",
                                    token=False,
                                    authors=False,
    )
            subjects_list = [record_metadata["subjects"][subject_idx]["subject"].lower() for subject_idx in range(len(record_metadata["subjects"]))]
            self.assertEqual(len(subjects_list), len(set(subjects_list)), 
                            f"Found duplicate subjects in record {record_id}")
    
    


if __name__ == '__main__':
    unittest.main()