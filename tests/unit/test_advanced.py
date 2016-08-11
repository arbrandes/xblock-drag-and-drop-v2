# Imports ###########################################################

import json
import unittest

from xblockutils.resources import ResourceLoader

from ..utils import make_block, TestCaseMixin


# Globals ###########################################################

loader = ResourceLoader(__name__)


# Classes ###########################################################

class BaseDragAndDropAjaxFixture(TestCaseMixin):
    ZONE_1 = None
    ZONE_2 = None

    FEEDBACK = {
        0: {"correct": None, "incorrect": None},
        1: {"correct": None, "incorrect": None},
        2: {"correct": None, "incorrect": None}
    }

    FINAL_FEEDBACK = None

    FOLDER = None

    def setUp(self):
        self.patch_workbench()
        self.block = make_block()
        initial_settings = self.initial_settings()
        for field in initial_settings:
            setattr(self.block, field, initial_settings[field])
        self.block.data = self.initial_data()

    @classmethod
    def initial_data(cls):
        return json.loads(loader.load_unicode('data/{}/data.json'.format(cls.FOLDER)))

    @classmethod
    def initial_settings(cls):
        return json.loads(loader.load_unicode('data/{}/settings.json'.format(cls.FOLDER)))

    @classmethod
    def expected_configuration(cls):
        return json.loads(loader.load_unicode('data/{}/config_out.json'.format(cls.FOLDER)))

    @classmethod
    def initial_feedback(cls):
        """ The initial overall_feedback value """
        return cls.expected_configuration()["initial_feedback"]

    def test_get_configuration(self):
        self.assertEqual(self.block.get_configuration(), self.expected_configuration())


class StandardModeFixture(BaseDragAndDropAjaxFixture):
    """
    Common tests for drag and drop in standard mode
    """
    def test_do_attempt_wrong_with_feedback(self):
        item_id, zone_id = 0, self.ZONE_2
        data = {"val": item_id, "zone": zone_id}
        res = self.call_handler('do_attempt', data)
        self.assertEqual(res, {
            "overall_feedback": None,
            "finished": False,
            "correct": False,
            "feedback": self.FEEDBACK[item_id]["incorrect"]
        })

    def test_do_attempt_wrong_without_feedback(self):
        item_id, zone_id = 2, self.ZONE_1
        data = {"val": item_id, "zone": zone_id}
        res = self.call_handler('do_attempt', data)
        self.assertEqual(res, {
            "overall_feedback": None,
            "finished": False,
            "correct": False,
            "feedback": self.FEEDBACK[item_id]["incorrect"]
        })

    def test_do_attempt_correct(self):
        item_id, zone_id = 0, self.ZONE_1
        data = {"val": item_id, "zone": zone_id}
        res = self.call_handler('do_attempt', data)
        self.assertEqual(res, {
            "overall_feedback": None,
            "finished": False,
            "correct": True,
            "feedback": self.FEEDBACK[item_id]["correct"]
        })

    def test_grading(self):
        published_grades = []

        def mock_publish(self, event, params):
            if event == 'grade':
                published_grades.append(params)
        self.block.runtime.publish = mock_publish

        self.call_handler('do_attempt', {
            "val": 0, "zone": self.ZONE_1
        })

        self.assertEqual(1, len(published_grades))
        self.assertEqual({'value': 0.5, 'max_value': 1}, published_grades[-1])

        self.call_handler('do_attempt', {
            "val": 1, "zone": self.ZONE_2
        })

        self.assertEqual(2, len(published_grades))
        self.assertEqual({'value': 1, 'max_value': 1}, published_grades[-1])

    def test_do_attempt_final(self):
        data = {"val": 0, "zone": self.ZONE_1}
        self.call_handler('do_attempt', data)

        expected_state = {
            "items": {
                "0": {"correct": True, "zone": self.ZONE_1}
            },
            "finished": False,
            "num_attempts": 0,
            'overall_feedback': self.initial_feedback(),
        }
        self.assertEqual(expected_state, self.call_handler('get_user_state', method="GET"))

        data = {"val": 1, "zone": self.ZONE_2}
        res = self.call_handler('do_attempt', data)
        self.assertEqual(res, {
            "overall_feedback": self.FINAL_FEEDBACK,
            "finished": True,
            "correct": True,
            "feedback": self.FEEDBACK[1]["correct"]
        })

        expected_state = {
            "items": {
                "0": {"correct": True, "zone": self.ZONE_1},
                "1": {"correct": True, "zone": self.ZONE_2}
            },
            "finished": True,
            "num_attempts": 0,
            'overall_feedback': self.FINAL_FEEDBACK,
        }
        self.assertEqual(expected_state, self.call_handler('get_user_state', method="GET"))


class AssessmentModeFixture(BaseDragAndDropAjaxFixture):
    """
    Common tests for drag and drop in assessment mode
    """
    def test_do_attempt_in_assessment_mode(self):
        item_id, zone_id = 0, self.ZONE_1
        data = {"val": item_id, "zone": zone_id, "x_percent": "33%", "y_percent": "11%"}
        res = self.call_handler('do_attempt', data)
        # In assessment mode, the do_attempt doesn't return any data.
        self.assertEqual(res, {})


class TestDragAndDropHtmlData(StandardModeFixture, unittest.TestCase):
    FOLDER = "html"

    ZONE_1 = "Zone <i>1</i>"
    ZONE_2 = "Zone <b>2</b>"

    FEEDBACK = {
        0: {"correct": "Yes <b>1</b>", "incorrect": "No <b>1</b>"},
        1: {"correct": "Yes <i>2</i>", "incorrect": "No <i>2</i>"},
        2: {"correct": "", "incorrect": ""}
    }

    FINAL_FEEDBACK = "Final <strong>feedback</strong>!"


class TestDragAndDropPlainData(StandardModeFixture, unittest.TestCase):
    FOLDER = "plain"

    ZONE_1 = "zone-1"
    ZONE_2 = "zone-2"

    FEEDBACK = {
        0: {"correct": "Yes 1", "incorrect": "No 1"},
        1: {"correct": "Yes 2", "incorrect": "No 2"},
        2: {"correct": "", "incorrect": ""}
    }

    FINAL_FEEDBACK = "This is the final feedback."


class TestOldDataFormat(TestDragAndDropPlainData):
    """
    Make sure we can work with the slightly-older format for 'data' field values.
    """
    FOLDER = "old"
    FINAL_FEEDBACK = "Final Feed"

    ZONE_1 = "Zone 1"
    ZONE_2 = "Zone 2"


class TestDragAndDropAssessmentData(AssessmentModeFixture, unittest.TestCase):
    FOLDER = "assessment"

    ZONE_1 = "zone-1"
    ZONE_2 = "zone-2"

    FEEDBACK = {
        0: {"correct": "Yes 1", "incorrect": "No 1"},
        1: {"correct": "Yes 2", "incorrect": "No 2"},
        2: {"correct": "", "incorrect": ""}
    }

    FINAL_FEEDBACK = "This is the final feedback."
