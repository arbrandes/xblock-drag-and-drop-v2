import ddt
import unittest

from drag_and_drop_v2.drag_and_drop_v2 import DragAndDropBlock
from drag_and_drop_v2.default_data import (
    TARGET_IMG_DESCRIPTION, TOP_ZONE_ID, MIDDLE_ZONE_ID, BOTTOM_ZONE_ID,
    START_FEEDBACK, FINISH_FEEDBACK, DEFAULT_DATA
)
from ..utils import make_block, TestCaseMixin


@ddt.ddt
class BasicTests(TestCaseMixin, unittest.TestCase):
    """ Basic unit tests for the Drag and Drop block, using its default settings """

    def setUp(self):
        self.block = make_block()
        self.patch_workbench()

    def _make_submission(self, modify_submission=None):
        modify = modify_submission if modify_submission else lambda x: x

        submission = {
            'display_name': "Test Drag & Drop",
            'mode': DragAndDropBlock.STANDARD_MODE,
            'max_attempts': 1,
            'show_title': False,
            'problem_text': "Problem Drag & Drop",
            'show_problem_header': False,
            'item_background_color': 'cornflowerblue',
            'item_text_color': 'coral',
            'weight': '5',
            'data': {
                'foo': 1,
                'items': []
            },
        }

        modify(submission)

        return submission

    def test_template_contents(self):
        context = {}
        student_fragment = self.block.runtime.render(self.block, 'student_view', context)
        self.assertIn('<section class="themed-xblock xblock--drag-and-drop">', student_fragment.content)
        self.assertIn('Loading drag and drop problem.', student_fragment.content)

    def test_get_configuration(self):
        """
        Test the get_configuration() method.
        The result of this method is passed to the block's JavaScript during initialization.
        """
        config = self.block.get_configuration()
        zones = config.pop("zones")
        items = config.pop("items")
        self.assertEqual(config, {
            "mode": DragAndDropBlock.STANDARD_MODE,
            "max_attempts": None,
            "display_zone_borders": False,
            "display_zone_labels": False,
            "title": "Drag and Drop",
            "show_title": True,
            "problem_text": "",
            "max_items_per_zone": None,
            "show_problem_header": True,
            "target_img_expanded_url": '/expanded/url/to/drag_and_drop_v2/public/img/triangle.png',
            "target_img_description": TARGET_IMG_DESCRIPTION,
            "item_background_color": None,
            "item_text_color": None,
            "initial_feedback": START_FEEDBACK,
            "url_name": "",
        })
        self.assertEqual(zones, DEFAULT_DATA["zones"])
        # Items should contain no answer data:
        self.assertEqual(items, [
            {"id": i, "displayName": display_name, "imageURL": "", "expandedImageURL": ""}
            for i, display_name in enumerate(
                [
                    "Goes to the top",
                    "Goes to the middle",
                    "Goes to the bottom",
                    "Goes anywhere",
                    "I don't belong anywhere"
                ]
            )
        ])

    def test_ajax_solve_and_reset(self):
        # Check assumptions / initial conditions:
        self.assertFalse(self.block.completed)

        def assert_user_state_empty():
            self.assertEqual(self.block.item_state, {})
            self.assertEqual(self.call_handler("get_user_state"), {
                'items': {},
                'finished': False,
                "num_attempts": 0,
                'overall_feedback': START_FEEDBACK,
            })
        assert_user_state_empty()

        # Drag three items into the correct spot:
        data = {"val": 0, "zone": TOP_ZONE_ID}
        self.call_handler('do_attempt', data)
        data = {"val": 1, "zone": MIDDLE_ZONE_ID}
        self.call_handler('do_attempt', data)
        data = {"val": 2, "zone": BOTTOM_ZONE_ID}
        self.call_handler('do_attempt', data)
        data = {"val": 3, "zone": MIDDLE_ZONE_ID}
        self.call_handler('do_attempt', data)

        # Check the result:
        self.assertTrue(self.block.completed)
        self.assertEqual(self.block.item_state, {
            '0': {'correct': True, 'zone': TOP_ZONE_ID},
            '1': {'correct': True, 'zone': MIDDLE_ZONE_ID},
            '2': {'correct': True, 'zone': BOTTOM_ZONE_ID},
            '3': {'correct': True, "zone": MIDDLE_ZONE_ID},
        })
        self.assertEqual(self.call_handler('get_user_state'), {
            'items': {
                '0': {'correct': True, 'zone': TOP_ZONE_ID},
                '1': {'correct': True, 'zone': MIDDLE_ZONE_ID},
                '2': {'correct': True, 'zone': BOTTOM_ZONE_ID},
                '3': {'correct': True, "zone": MIDDLE_ZONE_ID},
            },
            'finished': True,
            "num_attempts": 0,
            'overall_feedback': FINISH_FEEDBACK,
        })

        # Reset to initial conditions
        self.call_handler('reset', {})
        self.assertTrue(self.block.completed)
        assert_user_state_empty()

    def test_studio_submit(self):
        body = self._make_submission()
        res = self.call_handler('studio_submit', body)
        self.assertEqual(res, {'result': 'success'})

        self.assertEqual(self.block.show_title, False)
        self.assertEqual(self.block.mode, DragAndDropBlock.STANDARD_MODE)
        self.assertEqual(self.block.max_attempts, 1)
        self.assertEqual(self.block.display_name, "Test Drag & Drop")
        self.assertEqual(self.block.question_text, "Problem Drag & Drop")
        self.assertEqual(self.block.show_question_header, False)
        self.assertEqual(self.block.item_background_color, "cornflowerblue")
        self.assertEqual(self.block.item_text_color, "coral")
        self.assertEqual(self.block.weight, 5)
        self.assertEqual(self.block.max_items_per_zone, None)
        self.assertEqual(self.block.data, {'foo': 1, 'items': []})

    def test_studio_submit_assessment(self):
        def update_submission(submission):
            submission.update({
                'mode': DragAndDropBlock.ASSESSMENT_MODE,
                'max_items_per_zone': 4,
                'show_problem_header': True,
                'show_title': True,
                'max_attempts': 12,
                'item_text_color': 'red',
                'data': {'foo': 2, 'items': [{'zone': '1', 'title': 'qwe'}]},
            })

        body = self._make_submission(update_submission)
        res = self.call_handler('studio_submit', body)
        self.assertEqual(res, {'result': 'success'})

        self.assertEqual(self.block.show_title, True)
        self.assertEqual(self.block.mode, DragAndDropBlock.ASSESSMENT_MODE)
        self.assertEqual(self.block.max_attempts, 12)
        self.assertEqual(self.block.display_name, "Test Drag & Drop")
        self.assertEqual(self.block.question_text, "Problem Drag & Drop")
        self.assertEqual(self.block.show_question_header, True)
        self.assertEqual(self.block.item_background_color, "cornflowerblue")
        self.assertEqual(self.block.item_text_color, "red")
        self.assertEqual(self.block.weight, 5)
        self.assertEqual(self.block.max_items_per_zone, 4)
        self.assertEqual(self.block.data, {'foo': 2, 'items': [{'zone': '1', 'title': 'qwe'}]})

    def test_studio_submit_empty_max_items(self):
        def update_submission(submission):
            submission['max_items_per_zone'] = ''

        body = self._make_submission(update_submission)
        res = self.call_handler('studio_submit', body)
        self.assertEqual(res, {'result': 'success'})

        self.assertIsNone(self.block.max_items_per_zone)

    @ddt.data(-1, -5, -100, -1e15)
    def test_studio_submit_max_items_negative(self, max_items_per_zone):
        def modify_submission(submission):
            submission['max_items_per_zone'] = max_items_per_zone

        res = self.call_handler('studio_submit', self._make_submission(modify_submission))
        self.assertEqual(res['result'], 'failure')
        self.assertEqual(len(res['messages']), 1)
        self.assertIn('should be positive', res['messages'][0])

    def test_studio_submit_max_items_validation(self):
        def submission_success(submission):
            submission['max_items_per_zone'] = 1
            submission['data']['items'] = [
                {'zones': ['1'], 'title': 'item 1'}, {'zones': ['2'], 'title': 'item 2'}
            ]

        def submission_failure(submission):
            submission['max_items_per_zone'] = 1
            submission['data']['items'] = [
                {'zones': ['Zone 1'], 'title': 'item 1'}, {'zones': ['Zone 1'], 'title': 'item 2'}
            ]

        def submission_success2(submission):
            submission['max_items_per_zone'] = 2
            submission['data']['items'] = [
                {'zones': ['Zone 1'], 'title': 'item 1'},
                {'zones': ['Zone 1'], 'title': 'item 2'}
            ]

        def submission_failure2(submission):
            submission['max_items_per_zone'] = 1
            submission['data']['items'] = [
                {'zones': ['Zone 2'], 'title': 'item 1'},
                {'zones': ['Zone 2'], 'title': 'item 2'},
                {'zones': ['Zone 3'], 'title': 'item 3'},
                {'zones': ['Zone 3'], 'title': 'item 4'},
            ]

        res = self.call_handler('studio_submit', self._make_submission(submission_success))
        self.assertEqual(res, {'result': 'success'})

        res = self.call_handler('studio_submit', self._make_submission(submission_success2))
        self.assertEqual(res, {'result': 'success'})

        res = self.call_handler('studio_submit', self._make_submission(submission_failure))
        self.assertEqual(res['result'], 'failure')
        self.assertEqual(len(res['messages']), 1)
        self.assertIn("Zone 1", res['messages'][0])

        res = self.call_handler('studio_submit', self._make_submission(submission_failure2))
        self.assertEqual(res['result'], 'failure')
        self.assertEqual(len(res['messages']), 2)
        self.assertIn("Zone 2", res['messages'][0])
        self.assertIn("Zone 3", res['messages'][1])

    def test_expand_static_url(self):
        """ Test the expand_static_url handler needed in Studio when changing the image """
        res = self.call_handler('expand_static_url', '/static/blah.png')
        self.assertEqual(res, {'url': '/course/test-course/assets/blah.png'})

    def test_image_url(self):
        """ Ensure that the default image and custom URLs are both expanded by the runtime """
        self.assertEqual(self.block.data.get("targetImg"), None)
        self.assertEqual(
            self.block.get_configuration()["target_img_expanded_url"],
            '/expanded/url/to/drag_and_drop_v2/public/img/triangle.png',
        )

        self.block.data["targetImg"] = "/static/foo.png"
        self.assertEqual(
            self.block.get_configuration()["target_img_expanded_url"],
            '/course/test-course/assets/foo.png',
        )
