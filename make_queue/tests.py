from django.test import TestCase
from make_queue.models import Printer3D, Reservation3D, Quota3D
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta


class Reservation3DTestCase(TestCase):
    def setUp(self):
        Printer3D.objects.create(name="C1", location="Printer room Makerspace U1", status="F")
        user = User.objects.create_user("User", "user@makentnu.no", "user_pass")
        user.save()
        Quota3D.objects.create(user=user, can_print=True, max_time_reservation=10, max_number_of_reservations=2)

    def test_can_create_reservation(self):
        printer = Printer3D.objects.get(name="C1")
        user = User.objects.get(username="User")

        reservation = Reservation3D(user=user, printer=printer,
                                    start_time=timezone.now(), end_time=timezone.now() + timedelta(hours=2),
                                    event=False)

        self.assertTrue(reservation.validate())
        try:
            reservation.save()
        except ValidationError:
            self.fail("Could not save a valid reservation")

    def test_user_that_cannot_print_cannot_reserve(self):
        printer = Printer3D.objects.get(name="C1")
        user = User.objects.get(username="User")
        user_quota = user.quota3d
        user_quota.can_print = False
        user_quota.save()

        reservation = Reservation3D(user=user, printer=printer,
                                    start_time=timezone.now(), end_time=timezone.now() + timedelta(hours=2),
                                    event=False)

        self.assertFalse(reservation.validate())
        try:
            reservation.save()
            self.fail("Saving an invalid reservation should throw a ValidationError")
        except ValidationError:
            pass

    def test_reserve_longer_than_maximum_user_time(self):
        printer = Printer3D.objects.get(name="C1")
        user = User.objects.get(username="User")

        reservation = Reservation3D(user=user, printer=printer,
                                    start_time=timezone.now(),
                                    end_time=timezone.now() + timedelta(hours=user.quota3d.max_time_reservation + 0.1),
                                    event=False)

        self.assertFalse(reservation.validate())
        try:
            reservation.save()
            self.fail("Saving a reservation longer than the maximum allowed time for that user")
        except ValidationError:
            pass

    def test_reserve_end_time_before_start_time(self):
        printer = Printer3D.objects.get(name="C1")
        user = User.objects.get(username="User")

        reservation = Reservation3D(user=user, printer=printer,
                                    start_time=timezone.now(), end_time=timezone.now() - timedelta(hours=1),
                                    event=False)

        self.assertFalse(reservation.validate())
        try:
            reservation.save()
            self.fail("Saving a reservation with end time before start time should fail")
        except ValidationError:
            pass
