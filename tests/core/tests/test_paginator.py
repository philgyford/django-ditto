# coding: utf-8
from django.core import paginator as django_paginator
from django.test import TestCase

from ditto.core.paginator import DiggPaginator


class PaginatorTestCase(TestCase):

    def test_page_string(self):
        p = DiggPaginator(range(1,1000), 10, body=5).page(1)
        self.assertEqual(str(p), '1 2 3 4 5 ... 99 100')

    def test_error_with_string_page_number(self):
        with self.assertRaises(django_paginator.PageNotAnInteger):
            DiggPaginator(range(1,1000), 10, body=5).page('foo')

    def test_error_with_too_high_page_number(self):
        with self.assertRaises(django_paginator.EmptyPage):
            DiggPaginator(range(1,1000), 10, body=5).page(999)

    def test_softlimit(self):
        p = DiggPaginator(range(1,1000), 10, body=5).page(999, softlimit=True)
        self.assertEqual(p.number, 100)


    def test_odd_body_length_1(self):
        p = DiggPaginator(range(1,1000), 10, body=5).page(1)
        self.assertEqual(p.number, 1)
        self.assertEqual(p.page_range, [1, 2, 3, 4, 5, False, 99, 100])

    def test_odd_body_length_100(self):
        p = DiggPaginator(range(1,1000), 10, body=5).page(100)
        self.assertEqual(p.number, 100)
        self.assertEqual(p.page_range, [1, 2, False, 96, 97, 98, 99, 100])

    def test_even_body_length_1(self):
        p = DiggPaginator(range(1,1000), 10, body=6).page(1)
        self.assertEqual(p.number, 1)
        self.assertEqual(p.page_range, [1, 2, 3, 4, 5, 6, False, 99, 100])

    def test_even_body_length_100(self):
        p = DiggPaginator(range(1,1000), 10, body=6).page(100)
        self.assertEqual(p.number, 100)
        self.assertEqual(p.page_range, [1, 2, False, 95, 96, 97, 98, 99, 100])


    def test_combine_leading_range_1(self):
        p = DiggPaginator(
                        range(1,1000), 10, body=5, padding=2, margin=2).page(3)
        self.assertEqual(p.number, 3)
        self.assertEqual(p.page_range, [1, 2, 3, 4, 5, False, 99, 100])

    def test_combine_leading_range_2(self):
        p = DiggPaginator(
                        range(1,1000), 10, body=6, padding=2, margin=2).page(4)
        self.assertEqual(p.number, 4)
        self.assertEqual(p.page_range, [1, 2, 3, 4, 5, 6, False, 99, 100])

    def test_combine_leading_range_3(self):
        p = DiggPaginator(
                        range(1,1000), 10, body=5, padding=1, margin=2).page(6)
        self.assertEqual(p.number, 6)
        self.assertEqual(p.page_range, [1, 2, 3, 4, 5, 6, 7, False, 99, 100])

    def test_combine_leading_range_4(self):
        p = DiggPaginator(
                        range(1,1000), 10, body=5, padding=2, margin=2).page(7)
        self.assertEqual(p.number, 7)
        self.assertEqual(p.page_range,
                                [1, 2, False, 5, 6, 7, 8, 9, False, 99, 100])

    def test_combine_leading_range_5(self):
        p = DiggPaginator(
                        range(1,1000), 10, body=5, padding=1, margin=2).page(7)
        self.assertEqual(p.number, 7)
        self.assertEqual(p.page_range,
                                [1, 2, False, 5, 6, 7, 8, 9, False, 99, 100])


    def test_combine_trailing_range_1(self):
        p = DiggPaginator(
                    range(1,1000), 10, body=5, padding=2, margin=2).page(98)
        self.assertEqual(p.number, 98)
        self.assertEqual(p.page_range,
                            [1, 2, False, 96, 97, 98, 99, 100])

    def test_combine_trailing_range_2(self):
        p = DiggPaginator(
                    range(1,1000), 10, body=6, padding=2, margin=2).page(97)
        self.assertEqual(p.number, 97)
        self.assertEqual(p.page_range,
                            [1, 2, False, 95, 96, 97, 98, 99, 100])

    def test_combine_trailing_range_3(self):
        p = DiggPaginator(
                    range(1,1000), 10, body=5, padding=1, margin=2).page(95)
        self.assertEqual(p.number, 95)
        self.assertEqual(p.page_range,
                            [1, 2, False, 94, 95, 96, 97, 98, 99, 100])

    def test_combine_trailing_range_4(self):
        p = DiggPaginator(
                    range(1,1000), 10, body=5, padding=2, margin=2).page(94)
        self.assertEqual(p.number, 94)
        self.assertEqual(p.page_range,
                            [1, 2, False, 92, 93, 94, 95, 96, False, 99, 100])

    def test_combine_trailing_range_5(self):
        p = DiggPaginator(
                    range(1,1000), 10, body=5, padding=1, margin=2).page(94)
        self.assertEqual(p.number, 94)
        self.assertEqual(p.page_range,
                            [1, 2, False, 92, 93, 94, 95, 96, False, 99, 100])


    def test_combine_all_ranges_1(self):
        p = DiggPaginator(range(1,151), 10, body=6, padding=2).page(7)
        self.assertEqual(p.number, 7)
        self.assertEqual(p.page_range,
                        [1, 2, 3, 4, 5, 6, 7, 8, 9, False, 14, 15])

    def test_combine_all_ranges_2(self):
        p = DiggPaginator(range(1,151), 10, body=6, padding=2).page(8)
        self.assertEqual(p.number, 8)
        self.assertEqual(p.page_range,
                        [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15])

    def test_combine_all_ranges_3(self):
        p = DiggPaginator(range(1,151), 10, body=6, padding=1).page(8)
        self.assertEqual(p.number, 8)
        self.assertEqual(p.page_range,
                        [1, 2, 3, 4, 5, 6, 7, 8, 9, False, 14, 15])


    def test_no_leading_or_trainling_ranges_1(self):
        p = DiggPaginator(range(1,80), 10, body=10).page(1)
        self.assertEqual(p.number, 1)
        self.assertEqual(p.page_range, [1, 2, 3, 4, 5, 6, 7, 8])

    def test_no_leading_or_trainling_ranges_2(self):
        p = DiggPaginator(range(1,80), 10, body=10).page(8)
        self.assertEqual(p.number, 8)
        self.assertEqual(p.page_range, [1, 2, 3, 4, 5, 6, 7, 8])

    def test_no_leading_or_trainling_ranges_3(self):
        p = DiggPaginator(range(1,12), 10, body=5).page(1)
        self.assertEqual(p.number, 1)
        self.assertEqual(p.page_range, [1, 2])


    def test_left_align_mode_1(self):
        p = DiggPaginator(range(1,1000), 10, body=5, align_left=True).page(1)
        self.assertEqual(p.number, 1)
        self.assertEqual(p.page_range, [1, 2, 3, 4, 5])

    def test_left_align_mode_2(self):
        p = DiggPaginator(range(1,1000), 10, body=5, align_left=True).page(50)
        self.assertEqual(p.number, 50)
        self.assertEqual(p.page_range, [1, 2, False, 48, 49, 50, 51, 52])

    def test_left_align_mode_3(self):
        p = DiggPaginator(range(1,1000), 10, body=5, align_left=True).page(97)
        self.assertEqual(p.number, 97)
        self.assertEqual(p.page_range, [1, 2, False, 95, 96, 97, 98, 99])

    def test_left_align_mode_4(self):
        p = DiggPaginator(range(1,1000), 10, body=5, align_left=True).page(100)
        self.assertEqual(p.number, 100)
        self.assertEqual(p.page_range, [1, 2, False, 96, 97, 98, 99, 100])


    def test_default_padding(self):
        self.assertEqual(4, DiggPaginator(range(1,1000), 10, body=10).padding)

    def test_automatic_padding_reduction_1(self):
        self.assertEqual(2, DiggPaginator(range(1,1000), 10, body=5).padding)

    def test_automatic_padding_reduction_2(self):
        self.assertEqual(2, DiggPaginator(range(1,1000), 10, body=6).padding)


    def test_padding_sanity_check(self):
        with self.assertRaises(ValueError):
            DiggPaginator(range(1,1000), 10, body=5, padding=3)

