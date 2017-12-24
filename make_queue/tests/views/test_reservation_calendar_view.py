from django.test import TestCase
from datetime import datetime
from make_queue.views import ReservationCalendarView


class ReservationCalendarViewTestCase(TestCase):

    def test_year_and_week_to_monday(self):
        date = datetime(2017, 12, 18)
        self.assertEqual(date, ReservationCalendarView.year_and_week_to_monday(2017, 51))
