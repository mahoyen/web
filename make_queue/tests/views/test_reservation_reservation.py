from datetime import timedelta, time
from django.contrib.auth.models import User, Permission
from django.test import TestCase
from django.utils import timezone
from unittest.mock import patch

from make_queue.fields import MachineTypeField
from make_queue.models.course import Printer3DCourse
from make_queue.models.models import Machine, Quota, Reservation, ReservationRule
from make_queue.tests.utility import request_with_user, post_request_with_user, template_view_get_context_data
from make_queue.util.time import local_to_date
from make_queue.views.admin.reservation import AdminReservationView
from make_queue.views.reservation.reservation import MarkReservationAsDone
from news.models import Event, TimePlace


class ReservationAdminViewTest(TestCase):

    def test_get_admin_reservation(self):
        user = User.objects.create_user("test")
        machine_type = MachineTypeField.get_machine_type(1)
        Quota.objects.create(machine_type=machine_type, number_of_reservations=10, ignore_rules=True, user=user)
        permission = Permission.objects.get(codename="can_create_event_reservation")
        user.user_permissions.add(permission)
        event = Event.objects.create(title="Test_event")
        timeplace = TimePlace.objects.create(event=event, start_time=(timezone.now() + timedelta(hours=1)).time(),
                                             start_date=(timezone.now() + timedelta(hours=1)).date(),
                                             end_time=(timezone.now() + timedelta(hours=2)).time(),
                                             end_date=(timezone.now() + timedelta(hours=2)).date())
        printer = Machine.objects.create(machine_type=machine_type, machine_model="Ultimaker")
        Printer3DCourse.objects.create(user=user, username=user.username, name=user.get_full_name(),
                                       date=timezone.now())
        special_reservation = Reservation.objects.create(start_time=timezone.now() + timedelta(hours=1),
                                                         special_text="Test", special=True, user=user,
                                                         machine=printer, end_time=timezone.now() + timedelta(hours=2))
        normal_reservation = Reservation.objects.create(start_time=timezone.now() + timedelta(hours=2), user=user,
                                                        machine=printer, end_time=timezone.now() + timedelta(hours=3))
        event_reservation = Reservation.objects.create(start_time=timezone.now() + timedelta(hours=3), event=timeplace,
                                                       user=user, machine=printer,
                                                       end_time=timezone.now() + timedelta(hours=4))

        context_data = template_view_get_context_data(AdminReservationView, request_user=user)
        self.assertEqual(context_data["admin"], True)
        self.assertEqual(set(context_data["reservations"]), {special_reservation, event_reservation})


class MarkReservationAsDoneTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user("test")
        self.machine_type = MachineTypeField.get_machine_type(2)
        self.machine = Machine.objects.create(machine_type=self.machine_type, status="F", name="Test")
        Quota.objects.create(machine_type=self.machine_type, number_of_reservations=2, ignore_rules=False,
                             all=True)
        ReservationRule.objects.create(start_time=time(0, 0), end_time=time(23, 59), start_days=1, days_changed=6,
                                       max_inside_border_crossed=6, max_hours=6, machine_type=self.machine_type)

    def get_view(self):
        view = MarkReservationAsDone()
        view.request = request_with_user(self.user)
        return view

    def post_to_view(self, reservation):
        view = self.get_view()
        request = post_request_with_user(self.user, {"pk": reservation.pk})
        return view.post(request)

    def test_get(self):
        view = self.get_view()
        request = request_with_user(self.user)
        response = view.get(request)

        # Get is not allowed, so a redirect will be given
        self.assertEqual(302, response.status_code)

    @patch("django.utils.timezone.now")
    def test_post_valid(self, now_mock):
        now_mock.return_value = local_to_date(timezone.datetime(2018, 8, 12, 12, 0, 0))
        reservation = Reservation.objects.create(machine=self.machine, start_time=timezone.now() + timedelta(hours=1),
                                                 end_time=timezone.now() + timedelta(hours=2), user=self.user)
        now_mock.return_value = timezone.now() + timedelta(hours=1.1)
        self.assertTrue(reservation.can_change_end_time(self.user))
        response = self.post_to_view(reservation)

        # Will always be redirected
        self.assertEqual(302, response.status_code)
        self.assertEqual(Reservation.objects.get(pk=reservation.pk).end_time, timezone.now())

    def test_post_before_start(self):
        reservation = Reservation.objects.create(machine=self.machine, start_time=timezone.now() + timedelta(hours=1),
                                                 end_time=timezone.now() + timedelta(hours=2), user=self.user)

        response = self.post_to_view(reservation)
        self.assertEqual(302, response.status_code)
        self.assertEqual(reservation, Reservation.objects.get(pk=reservation.pk),
                         "Marking a reservation in the future as done, should not be possible")

    @patch("django.utils.timezone.now")
    def test_post_after_reservation(self, now_mock):
        now_mock.return_value = local_to_date(timezone.datetime(2018, 8, 12, 12, 0, 0))
        reservation = Reservation.objects.create(machine=self.machine, start_time=timezone.now() + timedelta(hours=1),
                                                 end_time=timezone.now() + timedelta(hours=2), user=self.user)
        now_mock.return_value = timezone.now() + timedelta(hours=3)
        response = self.post_to_view(reservation)
        self.assertEqual(302, response.status_code)
        self.assertEqual(reservation, Reservation.objects.get(pk=reservation.pk),
                         "Marking a reservation in the past as done should not do anything")

    @patch("django.utils.timezone.now")
    def test_special_case(self, now_mock):
        now_mock.return_value = local_to_date(timezone.datetime(2018, 11, 16, 10, 0, 0))
        reservation = Reservation.objects.create(machine=self.machine, start_time=timezone.now() + timedelta(minutes=1),
                                                 end_time=timezone.now() + timedelta(hours=6), user=self.user)
        reservation2 = Reservation.objects.create(machine=self.machine, start_time=timezone.now() + timedelta(hours=6),
                                                  end_time=timezone.now() + timedelta(hours=6, minutes=26),
                                                  user=User.objects.create_user("test2"))
        now_mock.return_value = local_to_date(timezone.datetime(2018, 11, 16, 15, 56, 0))
        response = self.post_to_view(reservation)
        self.assertEqual(302, response.status_code)
        self.assertEqual(timezone.now(), Reservation.objects.get(pk=reservation.pk).end_time)
