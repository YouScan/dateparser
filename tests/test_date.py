#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import unittest
from collections import OrderedDict
from datetime import datetime, timedelta

from mock import Mock, patch
from parameterized import parameterized, param
import six

import dateparser
from dateparser import date
from dateparser.date import get_last_day_of_month
from dateparser.conf import settings

from tests import BaseTestCase


class TestDateRangeFunction(BaseTestCase):
    def setUp(self):
        super(TestDateRangeFunction, self).setUp()
        self.result = NotImplemented

    @parameterized.expand([
        param(begin=datetime(2014, 6, 15), end=datetime(2014, 6, 25), expected_length=10)
    ])
    def test_date_range(self, begin, end, expected_length):
        self.when_date_range_generated(begin, end)
        self.then_range_length_is(expected_length)
        self.then_all_dates_in_range_are_present(begin, end)
        self.then_range_is_in_ascending_order()

    @parameterized.expand([
        param(begin=datetime(2014, 4, 15),
              end=datetime(2014, 6, 25),
              expected_months=[(2014, 4), (2014, 5), (2014, 6)]),
        param(begin=datetime(2014, 4, 25),
              end=datetime(2014, 5, 5),
              expected_months=[(2014, 4), (2014, 5)]),
        param(begin=datetime(2014, 4, 5),
              end=datetime(2014, 4, 25),
              expected_months=[(2014, 4)]),
        param(begin=datetime(2014, 4, 25),
              end=datetime(2014, 6, 5),
              expected_months=[(2014, 4), (2014, 5), (2014, 6)]),
    ])
    def test_one_date_for_each_month(self, begin, end, expected_months):
        self.when_date_range_generated(begin, end, months=1)
        self.then_expected_months_are(expected_months)

    @parameterized.expand([
        'year',
        'month',
        'week',
        'day',
        'hour',
        'minute',
        'second',
    ])
    def test_should_reject_easily_mistaken_dateutil_arguments(self, invalid_period):
        self.when_date_range_generated(begin=datetime(2014, 6, 15),
                                       end=datetime(2014, 6, 25),
                                       **{invalid_period: 1})
        self.then_period_was_rejected(invalid_period)

    def when_date_range_generated(self, begin, end, **size):
        try:
            self.result = list(date.date_range(begin, end, **size))
        except Exception as error:
            self.error = error

    def then_expected_months_are(self, expected):
        self.assertEqual(expected,
                         [(d.year, d.month) for d in self.result])

    def then_range_length_is(self, expected_length):
        self.assertEqual(expected_length, len(self.result))

    def then_all_dates_in_range_are_present(self, begin, end):
        date_under_test = begin
        while date_under_test < end:
            self.assertIn(date_under_test, self.result)
            date_under_test += timedelta(days=1)

    def then_range_is_in_ascending_order(self):
        for i in six.moves.range(len(self.result) - 1):
            self.assertLess(self.result[i], self.result[i + 1])

    def then_period_was_rejected(self, period):
        self.then_error_was_raised(ValueError, ['Invalid argument: {}'.format(period)])


class TestGetIntersectingPeriodsFunction(BaseTestCase):
    def setUp(self):
        super(TestGetIntersectingPeriodsFunction, self).setUp()
        self.result = NotImplemented

    @parameterized.expand([
        param(low=datetime(2014, 6, 15), high=datetime(2014, 6, 16), length=1)
    ])
    def test_date_arguments_and_date_range_with_default_post_days(self, low, high, length):
        self.when_intersecting_period_calculated(low, high, period_size='day')
        self.then_all_dates_in_range_are_present(begin=low, end=high)
        self.then_date_range_length_is(length)

    @parameterized.expand([
        param(low=datetime(2014, 4, 15),
              high=datetime(2014, 6, 25),
              expected_results=[datetime(2014, 4, 1), datetime(2014, 5, 1), datetime(2014, 6, 1)]),
        param(low=datetime(2014, 4, 25),
              high=datetime(2014, 5, 5),
              expected_results=[datetime(2014, 4, 1), datetime(2014, 5, 1)]),
        param(low=datetime(2014, 4, 5),
              high=datetime(2014, 4, 25),
              expected_results=[datetime(2014, 4, 1)]),
        param(low=datetime(2014, 4, 25),
              high=datetime(2014, 6, 5),
              expected_results=[datetime(2014, 4, 1), datetime(2014, 5, 1), datetime(2014, 6, 1)]),
        param(low=datetime(2014, 4, 25),
              high=datetime(2014, 4, 25),
              expected_results=[]),
        param(low=datetime(2014, 12, 31),
              high=datetime(2015, 1, 1),
              expected_results=[datetime(2014, 12, 1)]),
    ])
    def test_dates_in_intersecting_period_should_use_first_day_when_period_is_month(
        self, low, high, expected_results
    ):
        self.when_intersecting_period_calculated(low, high, period_size='month')
        self.then_results_are(expected_results)

    @parameterized.expand([
        param(low=datetime(2012, 4, 18),
              high=datetime(2014, 9, 22),
              expected_results=[datetime(2012, 1, 1, 0, 0), datetime(2013, 1, 1, 0, 0),
                                datetime(2014, 1, 1, 0, 0)]),
        param(low=datetime(2013, 8, 5),
              high=datetime(2014, 5, 15),
              expected_results=[datetime(2013, 1, 1, 0, 0), datetime(2014, 1, 1, 0, 0)]),
        param(low=datetime(2008, 4, 5),
              high=datetime(2010, 1, 1),
              expected_results=[datetime(2008, 1, 1, 0, 0), datetime(2009, 1, 1, 0, 0)]),
        param(low=datetime(2014, 1, 1),
              high=datetime(2016, 8, 22),
              expected_results=[datetime(2014, 1, 1, 0, 0), datetime(2015, 1, 1, 0, 0),
                                datetime(2016, 1, 1, 0, 0)]),
        param(low=datetime(2001, 7, 11),
              high=datetime(2001, 10, 16),
              expected_results=[datetime(2001, 1, 1, 0, 0)]),
        param(low=datetime(2017, 1, 1),
              high=datetime(2017, 1, 1),
              expected_results=[]),
    ])
    def test_dates_in_intersecting_period_should_use_first_month_and_first_day_when_period_is_year(
        self, low, high, expected_results
    ):
        self.when_intersecting_period_calculated(low, high, period_size='year')
        self.then_results_are(expected_results)

    @parameterized.expand([
        param(low=datetime(2014, 4, 15),
              high=datetime(2014, 5, 15),
              period_size='month',
              expected_results=[datetime(2014, 4, 1), datetime(2014, 5, 1)]),
        param(low=datetime(2014, 10, 30, 4, 30),
              high=datetime(2014, 11, 7, 5, 20),
              period_size='week',
              expected_results=[datetime(2014, 10, 27), datetime(2014, 11, 3)]),
        param(low=datetime(2014, 8, 13, 13, 21),
              high=datetime(2014, 8, 14, 14, 7),
              period_size='day',
              expected_results=[datetime(2014, 8, 13), datetime(2014, 8, 14)]),
        param(low=datetime(2014, 5, 11, 22, 4),
              high=datetime(2014, 5, 12, 0, 5),
              period_size='hour',
              expected_results=[datetime(2014, 5, 11, 22, 0),
                                datetime(2014, 5, 11, 23, 0),
                                datetime(2014, 5, 12, 0, 0)]),
        param(low=datetime(2014, 4, 25, 11, 11, 11),
              high=datetime(2014, 4, 25, 11, 12, 11),
              period_size='minute',
              expected_results=[datetime(2014, 4, 25, 11, 11, 0),
                                datetime(2014, 4, 25, 11, 12, 0)]),
        param(low=datetime(2014, 12, 31, 23, 59, 58, 500),
              high=datetime(2014, 12, 31, 23, 59, 59, 600),
              period_size='second',
              expected_results=[datetime(2014, 12, 31, 23, 59, 58, 0),
                                datetime(2014, 12, 31, 23, 59, 59, 0)]),
    ])
    def test_periods(self, low, high, period_size, expected_results):
        self.when_intersecting_period_calculated(low, high, period_size=period_size)
        self.then_results_are(expected_results)

    @parameterized.expand([
        param('years'),
        param('months'),
        param('days'),
        param('hours'),
        param('minutes'),
        param('seconds'),
        param('microseconds'),
        param('some_period'),
    ])
    def test_should_reject_easily_mistaken_dateutil_arguments(self, period_size):
        self.when_intersecting_period_calculated(low=datetime(2014, 6, 15),
                                                 high=datetime(2014, 6, 25),
                                                 period_size=period_size)
        self.then_error_was_raised(ValueError, ['Invalid period: ' + str(period_size)])

    @parameterized.expand([
        param(low=datetime(2014, 4, 15), high=datetime(2014, 4, 14), period_size='month'),
        param(low=datetime(2014, 4, 25), high=datetime(2014, 4, 25), period_size='month'),
    ])
    def test_empty_period(self, low, high, period_size):
        self.when_intersecting_period_calculated(low, high, period_size)
        self.then_period_is_empty()

    def when_intersecting_period_calculated(self, low, high, period_size):
        try:
            self.result = list(date.get_intersecting_periods(low, high, period=period_size))
        except Exception as error:
            self.error = error

    def then_results_are(self, expected_results):
        self.assertEquals(expected_results, self.result)

    def then_date_range_length_is(self, size):
        self.assertEquals(size, len(self.result))

    def then_all_dates_in_range_are_present(self, begin, end):
        date_under_test = begin
        while date_under_test < end:
            self.assertIn(date_under_test, self.result)
            date_under_test += timedelta(days=1)

    def then_period_is_empty(self):
        self.assertEquals([], self.result)


class TestParseWithFormatsFunction(BaseTestCase):
    def setUp(self):
        super(TestParseWithFormatsFunction, self).setUp()
        self.result = NotImplemented

    @parameterized.expand([
        param(date_string='yesterday', date_formats=['%Y-%m-%d']),
    ])
    def test_date_with_not_matching_format_is_not_parsed(self, date_string, date_formats):
        self.when_date_is_parsed_with_formats(date_string, date_formats)
        self.then_date_was_not_parsed()

    @parameterized.expand([
        param(date_string='25-03-14', date_formats=['%d-%m-%y'], expected_result=datetime(2014, 3, 25)),
    ])
    def test_should_parse_date(self, date_string, date_formats, expected_result):
        self.when_date_is_parsed_with_formats(date_string, date_formats)
        self.then_date_was_parsed()
        self.then_parsed_period_is('day')
        self.then_parsed_date_is(expected_result)

    @parameterized.expand([
        param(date_string='09.16', date_formats=['%m.%d'], expected_month=9, expected_day=16),
    ])
    def test_should_use_current_year_for_dates_without_year(
        self, date_string, date_formats, expected_month, expected_day
    ):
        self.given_now(2015, 2, 4)
        self.when_date_is_parsed_with_formats(date_string, date_formats)
        self.then_date_was_parsed()
        self.then_parsed_period_is('day')
        self.then_parsed_date_is(datetime(2015, expected_month, expected_day))

    @parameterized.expand([
        param(date_string='August 2014', date_formats=['%B %Y'],
              expected_year=2014, expected_month=8),
    ])
    def test_should_use_last_day_of_month_for_dates_without_day(
        self, date_string, date_formats, expected_year, expected_month
    ):
        self.given_now(2014, 8, 12)
        self.when_date_is_parsed_with_formats(date_string, date_formats)
        self.then_date_was_parsed()
        self.then_parsed_period_is('month')
        self.then_parsed_date_is(datetime(year=expected_year,
                                          month=expected_month,
                                          day=get_last_day_of_month(expected_year, expected_month)))

    def given_now(self, year, month, day, **time):
        now = datetime(year, month, day, **time)
        datetime_mock = Mock(wraps=datetime)
        datetime_mock.utcnow = Mock(return_value=now)
        datetime_mock.now = Mock(return_value=now)
        datetime_mock.today = Mock(return_value=now)
        self.add_patch(patch('dateparser.date.datetime', new=datetime_mock))

    def when_date_is_parsed_with_formats(self, date_string, date_formats):
        self.result = date.parse_with_formats(date_string, date_formats, settings)

    def then_date_was_not_parsed(self):
        self.assertIsNotNone(self.result)
        self.assertIsNone(self.result['date_obj'])

    def then_date_was_parsed(self):
        self.assertIsNotNone(self.result)
        self.assertIsNotNone(self.result['date_obj'])

    def then_parsed_date_is(self, date_obj):
        self.assertEquals(date_obj.date(), self.result['date_obj'].date())

    def then_parsed_period_is(self, period):
        self.assertEquals(period, self.result['period'])


class TestDateDataParser(BaseTestCase):
    def setUp(self):
        super(TestDateDataParser, self).setUp()
        self.parser = NotImplemented
        self.result = NotImplemented
        self.multiple_results = NotImplemented

    @parameterized.expand([
        param('10:04am EDT'),
    ])
    def test_time_without_date_should_use_today(self, date_string):
        self.given_parser(settings={'RELATIVE_BASE': datetime(2020, 7, 19)})
        self.when_date_string_is_parsed(date_string)
        self.then_date_was_parsed()
        self.then_parsed_date_is(datetime(2020, 7, 19).date())

    @parameterized.expand([
        # Today
        param('today', days_ago=0),
        param('Today', days_ago=0),
        param('TODAY', days_ago=0),
        param('Сегодня', days_ago=0),
        param('Hoje', days_ago=0),
        param('Oggi', days_ago=0),
        # Yesterday
        param('yesterday', days_ago=1),
        param(' Yesterday \n', days_ago=1),
        param('Ontem', days_ago=1),
        param('Ieri', days_ago=1),
        # Day before yesterday
        param('the day before yesterday', days_ago=2),
        param('The DAY before Yesterday', days_ago=2),
        param('Anteontem', days_ago=2),
        param('Avant-hier', days_ago=2),
        param(u'вчера', days_ago=1),
        param(u'снощи', days_ago=1)
    ])
    def test_temporal_nouns_are_parsed(self, date_string, days_ago):
        self.given_parser()
        self.when_date_string_is_parsed(date_string)
        self.then_date_was_parsed()
        self.then_date_is_n_days_ago(days=days_ago)

    def test_should_not_assume_language_too_early(self):
        dates_to_parse = OrderedDict([(u'07/07/2014', datetime(2014, 7, 7).date()),  # any language
                                      (u'07.jul.2014 | 12:52', datetime(2014, 7, 7).date()),  # en, es, pt, nl
                                      (u'07.ago.2014 | 12:52', datetime(2014, 8, 7).date()),  # es, it, pt
                                      (u'07.feb.2014 | 12:52', datetime(2014, 2, 7).date()),  # en, de, es, it, nl, ro
                                      (u'07.ene.2014 | 12:52', datetime(2014, 1, 7).date())])  # es

        self.given_parser(restrict_to_languages=['en', 'de', 'fr', 'it', 'pt',
                                                 'nl', 'ro', 'es', 'ru'])
        self.when_multiple_dates_are_parsed(dates_to_parse.keys())
        self.then_all_results_were_parsed()
        self.then_parsed_dates_are(list(dates_to_parse.values()))

    @parameterized.expand([
        param(date_string=u'11 Marzo, 2014', locale='es'),
        param(date_string=u'13 Septiembre, 2014', locale='es'),
        param(date_string=u'Сегодня', locale='ru'),
        param(date_string=u'Avant-hier', locale='fr'),
        param(date_string=u'Anteontem', locale='pt'),
        param(date_string=u'ธันวาคม 11, 2014, 08:55:08 PM', locale='th'),
        param(date_string=u'Anteontem', locale='pt'),
        param(date_string=u'14 aprilie 2014', locale='ro'),
        param(date_string=u'11 Ağustos, 2014', locale='tr'),
        param(date_string=u'pon 16. čer 2014 10:07:43', locale='cs'),
        param(date_string=u'24 януари 2015г.', locale='bg')
    ])
    def test_returned_detected_locale_should_be(self, date_string, locale):
        self.given_parser()
        self.when_date_string_is_parsed(date_string)
        self.then_detected_locale(locale)

    @parameterized.expand([
        param("2014-10-09T17:57:39+00:00"),
    ])
    def test_get_date_data_should_not_strip_timezone_info(self, date_string):
        self.given_parser()
        self.when_date_string_is_parsed(date_string)
        self.then_date_was_parsed()
        self.then_parsed_date_has_timezone()

    @parameterized.expand([
        param(date_string="14 giu 13", date_formats=["%y %B %d"],
              expected_result=datetime(2014, 6, 13)),
        param(date_string="14_luglio_15", date_formats=["%y_%B_%d"],
              expected_result=datetime(2014, 7, 15)),
        param(date_string="14_LUGLIO_15", date_formats=["%y_%B_%d"],
              expected_result=datetime(2014, 7, 15)),
        param(date_string="10.01.2016, 20:35", date_formats=["%d.%m.%Y, %H:%M"],
              expected_result=datetime(2016, 1, 10, 20, 35), expected_period='time'),
    ])
    def test_parse_date_using_format(self, date_string, date_formats, expected_result, expected_period='day'):
        self.given_local_tz_offset(0)
        self.given_parser()
        self.when_date_string_is_parsed(date_string, date_formats)
        self.then_date_was_parsed()
        self.then_period_is(expected_period)
        self.then_parsed_datetime_is(expected_result)

    @parameterized.expand([
        param(date_string="11/09/2007", date_formats={"date_formats": ["%d/%m/%Y"]}),
        param(date_string="16.09.03 11:55", date_formats=111),
        param(date_string="08-01-1998", date_formats=12.56),
    ])
    def test_parsing_date_using_invalid_type_date_format_must_raise_error(
            self, date_string, date_formats):
        self.given_local_tz_offset(0)
        self.given_parser()
        self.when_date_string_is_parsed(date_string, date_formats)
        self.then_error_was_raised(
            TypeError, ["Date formats should be list, tuple or set of strings",
                        "'{}' object is not iterable".format(type(date_formats).__name__)])

    @parameterized.expand([
        param(date_string={"date": "12/11/1998"}),
        param(date_string=[2017, 12, 1]),
        param(date_string=2018),
        param(date_string=12.2000),
        param(date_string=datetime(year=2009, month=12, day=7)),
    ])
    def test_parsing_date_using_invalid_type_date_string_must_raise_error(self, date_string):
        self.given_parser()
        self.when_date_string_is_parsed(date_string)
        self.then_error_was_raised(TypeError, ["Input type must be str or unicode"])

    @parameterized.expand([
        param(date_string="2014/11/17 14:56 EDT", expected_result=datetime(2014, 11, 17, 18, 56)),
    ])
    def test_parse_date_with_timezones_not_using_formats(self, date_string, expected_result):
        self.given_parser(settings={'TO_TIMEZONE': 'UTC'})
        self.when_date_string_is_parsed(date_string)
        self.then_date_was_parsed()
        self.then_period_is('time')
        self.result['date_obj'] = self.result['date_obj'].replace(tzinfo=None)
        self.then_parsed_datetime_is(expected_result)

    @parameterized.expand([
        param(date_string="2014/11/17 14:56 EDT",
              date_formats=["%Y/%m/%d %H:%M EDT"],
              expected_result=datetime(2014, 11, 17, 14, 56)),
    ])
    def test_parse_date_with_timezones_using_formats_ignore_timezone(
            self, date_string, date_formats, expected_result):
        self.given_local_tz_offset(0)
        self.given_parser()
        self.when_date_string_is_parsed(date_string, date_formats)
        self.then_date_was_parsed()
        self.then_period_is('time')
        self.then_parsed_datetime_is(expected_result)

    @parameterized.expand([
        param(date_string="08-08-2014\xa018:29", expected_result=datetime(2014, 8, 8, 18, 29)),
    ])
    def test_should_parse_with_no_break_space_in_dates(self, date_string, expected_result):
        self.given_parser()
        self.when_date_string_is_parsed(date_string)
        self.then_date_was_parsed()
        self.then_period_is('time')
        self.then_parsed_datetime_is(expected_result)

    @parameterized.expand([
        param(date_string="12 jan 1876",
              expected_result=(datetime(1876, 1, 12, 0, 0), 'day', 'en', ['day', 'month', 'year'])),
        param(date_string="02/09/16",
              expected_result=(datetime(2016, 2, 9, 0, 0), 'day', 'en', ['month', 'day', 'year'])),
        param(date_string="10 giu 2018",
              expected_result=(datetime(2018, 6, 10, 0, 0), 'day', 'it', ['day', 'month', 'year'])),
    ])
    def test_get_date_tuple(self, date_string, expected_result):
        self.given_parser()
        self.when_get_date_tuple_is_called(date_string)
        self.then_returned_tuple_is(expected_result)

    @parameterized.expand([
        param(date_string="22.05.2019 11:03",
              expected_date=datetime(2019, 5, 22, 11, 3),
              expected_period='time',
              expected_order=['day', 'month', 'year']),
    ])
    def test_inferred_order(self, date_string, expected_date, expected_period, expected_order):
        self.given_parser(settings={'DATE_ORDER': 'YMD'})
        self.when_date_string_is_parsed(date_string)
        self.then_parsed_datetime_is(expected_date)
        self.then_period_is(expected_period)
        self.then_returned_order_is(expected_order)

    def given_now(self, year, month, day, **time):
        datetime_mock = Mock(wraps=datetime)
        datetime_mock.utcnow = Mock(return_value=datetime(year, month, day, **time))
        self.add_patch(
            patch('dateparser.date_parser.datetime', new=datetime_mock)
        )

    def given_parser(self, restrict_to_languages=None, **params):
        self.parser = date.DateDataParser(languages=restrict_to_languages, **params)

    def given_local_tz_offset(self, offset):
        self.add_patch(
            patch.object(dateparser.timezone_parser,
                         'local_tz_offset',
                         new=timedelta(seconds=3600 * offset))
        )

    def when_date_string_is_parsed(self, date_string, date_formats=None):
        try:
            self.result = self.parser.get_date_data(date_string, date_formats)
        except Exception as error:
            self.error = error

    def when_multiple_dates_are_parsed(self, date_strings):
        self.multiple_results = []
        for date_string in date_strings:
            try:
                result = self.parser.get_date_data(date_string)
            except Exception as error:
                result = error
            finally:
                self.multiple_results.append(result)

    def when_get_date_tuple_is_called(self, date_string):
        self.result = self.parser.get_date_tuple(date_string)

    def then_date_was_parsed(self):
        self.assertIsNotNone(self.result['date_obj'])

    def then_date_locale(self):
        self.assertIsNotNone(self.result['locale'])

    def then_date_is_n_days_ago(self, days):
        today = datetime.now().date()
        expected_date = today - timedelta(days=days)
        self.assertEqual(expected_date, self.result['date_obj'].date())

    def then_all_results_were_parsed(self):
        self.assertNotIn(None, self.multiple_results)

    def then_parsed_dates_are(self, expected_dates):
        self.assertEqual(expected_dates,
                         [result['date_obj'].date() for result in self.multiple_results])

    def then_detected_locale(self, locale):
        self.assertEqual(locale, self.result['locale'])

    def then_period_is(self, day):
        self.assertEqual(day, self.result['period'])

    def then_parsed_datetime_is(self, expected_datetime):
        self.assertEqual(expected_datetime, self.result['date_obj'])

    def then_parsed_date_is(self, expected_date):
        self.assertEqual(expected_date, self.result['date_obj'].date())

    def then_parsed_date_has_timezone(self):
        self.assertTrue(hasattr(self.result['date_obj'], 'tzinfo'))

    def then_returned_tuple_is(self, expected_tuple):
        self.assertEqual(expected_tuple, self.result)

    def then_returned_order_is(self, expected_order):
        self.assertEqual(expected_order, self.result['inferred_order'])


class TestParserInitialization(BaseTestCase):
    def setUp(self):
        super(TestParserInitialization, self).setUp()
        self.parser = NotImplemented

    @parameterized.expand([
        param(languages='en'),
        param(languages={'languages': ['en', 'he', 'it']}),
    ])
    def test_error_raised_for_invalid_languages_argument(self, languages):
        self.when_parser_is_initialized(languages=languages)
        self.then_error_was_raised(
            TypeError, ["languages argument must be a list (%r given)" % type(languages)])

    @parameterized.expand([
        param(locales='en-001'),
        param(locales={'locales': ['zh-Hant-HK', 'ha-NE', 'se-SE']}),
    ])
    def test_error_raised_for_invalid_locales_argument(self, locales):
        self.when_parser_is_initialized(locales=locales)
        self.then_error_was_raised(
            TypeError, ["locales argument must be a list (%r given)" % type(locales)])

    @parameterized.expand([
        param(region=['AW', 'BE']),
        param(region=150),
    ])
    def test_error_raised_for_invalid_region_argument(self, region):
        self.when_parser_is_initialized(region=region)
        self.then_error_was_raised(
            TypeError, ["region argument must be str or unicode (%r given)" % type(region)])

    @parameterized.expand([
        param(try_previous_locales=['ar-OM', 'pt-PT', 'fr-CG', 'uk']),
        param(try_previous_locales='uk'),
        param(try_previous_locales={'try_previous_locales': True}),
        param(try_previous_locales=0),
    ])
    def test_error_raised_for_invalid_try_previous_locales_argument(self, try_previous_locales):
        self.when_parser_is_initialized(try_previous_locales=try_previous_locales)
        self.then_error_was_raised(
            TypeError, ["try_previous_locales argument must be a boolean (%r given)"
                        % type(try_previous_locales)])

    @parameterized.expand([
        param(use_given_order=['da', 'pt', 'ja', 'sv']),
        param(use_given_order='uk'),
        param(use_given_order={'use_given_order': True}),
        param(use_given_order=1),
    ])
    def test_error_raised_for_invalid_use_given_order_argument(self, use_given_order):
        self.when_parser_is_initialized(locales=['en', 'es'], use_given_order=use_given_order)
        self.then_error_was_raised(
            TypeError, ["use_given_order argument must be a boolean (%r given)"
                        % type(use_given_order)])

    def test_error_is_raised_when_use_given_order_is_True_and_locales_is_None(self):
        self.when_parser_is_initialized(use_given_order=True)
        self.then_error_was_raised(
            ValueError, ["locales must be given if use_given_order is True"])

    def when_parser_is_initialized(self, languages=None, locales=None, region=None,
                                   try_previous_locales=True, use_given_order=False):
        try:
            self.parser = date.DateDataParser(
                languages=languages, locales=locales, region=region,
                try_previous_locales=try_previous_locales, use_given_order=use_given_order)
        except Exception as error:
            self.error = error


class TestSanitizeDate(BaseTestCase):
    def test_remove_year_in_russian(self):
        self.assertEqual(date.sanitize_date(u'2005г.'), u'2005 ')
        self.assertEqual(date.sanitize_date(u'2005 г.'), u'2005 ')
        self.assertEqual(date.sanitize_date(u'Авг.'), u'Авг')


class TestDateLocaleParser(BaseTestCase):
    def setUp(self):
        super(TestDateLocaleParser, self).setUp()

    @parameterized.expand([
        param(date_obj={'date_obj': datetime(1999, 10, 1, 0, 0)}),
        param(date_obj={'period': 'day'}),
        param(date_obj={'date': datetime(2007, 1, 22, 0, 0), 'period': 'day'}),
        param(date_obj={'period': 'hour'}),
        param(date_obj=[datetime(2007, 1, 22, 0, 0), 'day']),
        param(date_obj={'date_obj': None, 'period': 'day'}),
    ])
    def test_is_valid_date_obj(self, date_obj):
        self.given_parser(language=['en'], date_string='10 jan 2000',
                          date_formats=None, settings=settings)
        self.when_date_object_is_validated(date_obj)
        self.then_date_object_is_invalid()

    def given_parser(self, language, date_string, date_formats, settings):
        self.parser = date._DateLocaleParser(language, date_string, date_formats, settings)

    def when_date_object_is_validated(self, date_obj):
        self.is_valid_date_obj = self.parser._is_valid_date_obj(date_obj)

    def then_date_object_is_invalid(self):
        self.assertFalse(self.is_valid_date_obj)


if __name__ == '__main__':
    unittest.main()
