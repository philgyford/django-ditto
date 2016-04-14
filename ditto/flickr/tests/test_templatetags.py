from django.test import TestCase

from freezegun import freeze_time

from ...ditto.templatetags.ditto import display_time
from ...ditto.utils import datetime_now
from ..templatetags import flickr


class TakenTimeTestCase(TestCase):

    @freeze_time("2015-08-14 13:34:56", tz_offset=-8)
    def setUp(self):
        self.dt = datetime_now()

    def test_taken_time_0(self):
        "taken_time() with granularity 0"
        self.assertEqual(flickr.taken_time(self.dt, 0),
                        '%s' % display_time(self.dt, True))

    def test_taken_time_4(self):
        "taken_time() with granularity 4"
        self.assertEqual(flickr.taken_time(self.dt, 4),
                        'Some time in August 2015')

    def test_taken_time_6(self):
        "taken_time() with granularity 6"
        self.assertEqual(flickr.taken_time(self.dt, 6),
                        'Some time in 2015')

    def test_taken_time_8(self):
        "taken_time() with granularity 8"
        self.assertEqual(flickr.taken_time(self.dt, 8),
                        'Circa 2015')

    def test_taken_time_9(self):
        "taken_time() with granularity 9"
        self.assertEqual(flickr.taken_time(self.dt, 9), '')


class PhotoLicenseTestCase(TestCase):

    def test_license_0(self):
        self.assertEqual(flickr.photo_license('0'), 'All Rights Reserved')

    def test_license_1(self):
        self.assertEqual(flickr.photo_license('1'),
            '<a href="https://creativecommons.org/licenses/by-nc-sa/2.0/" title="More about permissions">Attribution-NonCommercial-ShareAlike License</a>'
        )

    def test_license_99(self):
        self.assertEqual(flickr.photo_license('99'), '[missing]')


class PhotoSafetyLevelTestCase(TestCase):

    def test_safety_level_0(self):
        self.assertEqual(flickr.photo_safety_level(0), 'none')

    def test_safety_level_1(self):
        self.assertEqual(flickr.photo_safety_level(1), 'Safe')

    def test_safety_level_4(self):
        self.assertEqual(flickr.photo_safety_level(4), '[missing]')

