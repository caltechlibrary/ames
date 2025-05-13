import unittest
import random, os
from run_subject_id_correction import all_corrected 
from caltechdata_api import caltechdata_write

os.environ["RDMTOK"] = "FVyjwsxBvfNXm5NmmfL8fKGI8hhA6puT9pNJO8PAyrLlNYdeMjfjhBVvuhbs"


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
    # files=files,
    production=False,
    publish= True
)


    record_ids.append("" + response)






class TestSubjects(unittest.TestCase):
    
    def test_subject_changes(self):
        for i in range(len(record_ids)):
            self.assertEqual(all_corrected(record_ids[i]), True)

    

if __name__ == '__main__':
    unittest.main()
