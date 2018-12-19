from math import ceil

from django.core.exceptions import ValidationError
from django.http import HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.generic import RedirectView, FormView, CreateView, UpdateView

from make_queue.forms import FreeSlotForm, ReservationForm
from make_queue.models.models import Machine, Reservation, Quota
from make_queue.templatetags.reservation_extra import calendar_url_reservation
from make_queue.util.time import timedelta_to_hours


class ReservationCreateView(CreateView):
    form_class = ReservationForm
    template_name = "make_queue/reservation_create.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update(user=self.request.user, machine=self.kwargs.pop("machine", 0))
        return kwargs

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data.update({
            "max_days_in_advance": Reservation.reservation_future_limit_days,
        })
        return context_data

    def form_valid(self, form):
        # User is not included in form
        form.instance.user = self.request.user

        # Want to perform error checking to provide the user with some feedback
        try:
            self.object = form.save()
        except ValidationError:
            # If the user waits for too long, it is possible to use the form to create a reservation in the past
            if form.instance.start_time < timezone.now():
                form.add_error(None, _("It is not possible to create a reservation starting in the past."))
            # If the user tries to make a reservation when no Quota is available and free
            elif not Quota.can_make_reservation(form.instance):
                form.add_error(None, _("You have reached your maximum number of future reservations."))
            # Catch all case
            else:
                form.add_error(None, _(
                    "It was not possible to create the given reservation, as the time may already be reserved."))
            return self.form_invalid(form)
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return calendar_url_reservation(self.object)


class ReservationEditView(UpdateView):
    model = Reservation
    form_class = ReservationForm
    template_name = "make_queue/reservation_edit.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update(user=self.request.user)
        return kwargs

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data.update({
            # Users should not be able to change the start time of the reservation after it has started
            "disable_start_time": self.object.start_time < timezone.now(),
            "max_days_in_advance": Reservation.reservation_future_limit_days,
            "reservation": self.object.pk,
        })
        return context_data

    def form_valid(self, form):
        # Want to perform error checking to provide the user with some feedback
        try:
            self.object = form.save()
        except ValidationError:
            # This is the only major error that may occur on edit, without the user deliberately changing the JS or HTML
            if form.instance.end_time < timezone.now():
                form.add_error(None, _("It is not possible to set the end time of the reservation in the past."))
            return self.form_invalid(form)
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return calendar_url_reservation(self.object)


class DeleteReservationView(RedirectView):
    # TODO: Change to DeleteView
    """View for deleting a reservation (Cannot be DeleteView due to the abstract inheritance of reservations)"""
    http_method_names = ["post"]

    def get_redirect_url(self, *args, **kwargs):
        """
        Gives the redirect url for when the reservation is deleted
        :return: The redirect url
        """
        if "next" in self.request.POST:
            return self.request.POST.get("next")
        return reverse("my_reservations")

    def dispatch(self, request, *args, **kwargs):
        """
        Delete the reservation if it can be deleted by the current user and exists
        :param request: The HTTP POST request
        """
        if "pk" in request.POST:
            pk = request.POST.get("pk")

            try:
                reservation = Reservation.objects.get(pk=pk)
                if reservation.can_delete(request.user):
                    reservation.delete()
            except Reservation.DoesNotExist:
                pass

        return super().dispatch(request, *args, **kwargs)


class MarkReservationAsDone(RedirectView):
    url = reverse_lazy("my_reservations")

    def get_redirect_url(self, *args, next_url=None, **kwargs):
        if next_url is not None:
            return next_url
        return super().get_redirect_url(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        pk = request.POST.get("pk", default=0)
        reservations = Reservation.objects.filter(pk=pk)
        if not reservations.exists():
            return self.get(request, *args, **kwargs)

        reservation = reservations.first()
        if not reservation.can_change_end_time(request.user) or reservation.start_time >= timezone.now():
            return self.get(request, *args, **kwargs)

        reservation.end_time = timezone.now()
        reservation.save()

        return self.get(request, *args, **kwargs)


class FindFreeSlot(FormView):
    """
    View to find free time slots for reservations
    """
    template_name = "make_queue/find_free_slot.html"
    form_class = FreeSlotForm

    @staticmethod
    def format_period(machine, start_time, end_time):
        """
        Formats a time period for the context
        """
        return {
            "machine": machine,
            "start_time": start_time,
            "end_time": end_time,
            "duration": ceil(timedelta_to_hours(end_time - start_time))
        }

    def get_periods(self, machine, required_time):
        """
        Finds all future periods for the given machine with a minimum length

        :param machine: The machine to get periods for
        :param required_time: The minimum required time for the period
        :return: A list of periods
        """
        periods = []
        reservations = list(
            Reservation.objects.filter(end_time__gte=timezone.now(), machine__pk=machine.pk).order_by("start_time"))

        # Find all periods between reservations
        for period_start, period_end in zip(reservations, reservations[1:]):
            duration = timedelta_to_hours(period_end.start_time - period_start.end_time)
            if duration >= required_time:
                periods.append(self.format_period(machine, period_start.end_time, period_end.start_time))

        # Add remaining time after last reservation
        if reservations:
            periods.append(self.format_period(
                machine, reservations[-1].end_time,
                timezone.now() + timezone.timedelta(days=Reservation.reservation_future_limit_days)))
        # If the machine is not reserved anytime in the future, we include the whole allowed period
        else:
            periods.append(self.format_period(
                machine, timezone.now(),
                timezone.now() + timezone.timedelta(days=Reservation.reservation_future_limit_days)))
        return periods

    def form_valid(self, form):
        """
        Renders the page with free slots in respect to the valid form

        :param form: A valid FreeSlotForm form
        :return: A HTTP response rendering the page with the found free slots
        """
        context = self.get_context_data()

        # Time should be expressed in hours
        required_time = form.cleaned_data["hours"] + form.cleaned_data["minutes"] / 60

        periods = []
        for machine in Machine.objects.filter(machine_type=form.cleaned_data["machine_type"]):
            periods += self.get_periods(machine, required_time)

        # Periods in the near future is more interesting than in the distant future
        periods.sort(key=lambda period: period["start_time"])

        context.update({
            "free_slots": periods,
        })
        return self.render_to_response(context)
