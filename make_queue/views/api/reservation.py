from django.http import JsonResponse, HttpResponseBadRequest
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from make_queue.models.models import Reservation, Quota, ReservationRule, Machine
from make_queue.util.time import year_and_week_to_monday


def get_machine_data(request, machine, reservation=None):
    return JsonResponse({
        "reservations": [wrap_reservation(c_reservation, request.user) for c_reservation
                         in Reservation.objects.filter(end_time__gte=timezone.now(), machine=machine)
                         if c_reservation != reservation],
    })


def get_reservation_hover_text(reservation, user):
    if reservation.special:
        return {
            "header": _("Reservation"),
            "fields": [
                (_("Purpose"), reservation.special_text),
            ]
        }
    if not reservation.special and not reservation.event and user.has_perm("make_queue.can_view_reservation_user"):
        data = {
            "header": _("Reservation"),
            "fields": [
                (_("Name"), reservation.user.get_full_name()),
                (_("Email"), reservation.user.email),
                # TODO: Fix time formatting
                (_("Time"), "TODO"),
            ]
        }
        if reservation.comment:
            data["fields"].append((_("Comment"), reservation.comment))

        return data
    return []


def get_reservation_type(reservation, user):
    if reservation.event:
        return "event"
    if reservation.special:
        return "make"
    if reservation.user == user:
        return "user"
    return "normal"


def wrap_reservation(reservation, user):
    return {
        "start_time": reservation.start_time,
        "end_time": reservation.end_time,
        "popup": get_reservation_hover_text(reservation, user),
        "type": get_reservation_type(reservation, user),
    }


# TODO: Comment and test
def get_reservation_data(request):
    try:
        machine = Machine.objects.get(pk=request.GET.get("machine", 0))
    except Machine.DoesNotExist:
        return HttpResponseBadRequest("Machine was not given, or does not exist")

    year = request.GET.get("year", timezone.now().year)
    week = request.GET.get("week", timezone.now().isocalendar()[1])
    start_of_week = year_and_week_to_monday(year, week)

    data = {
        "year": year,
        "week": week,
        "canUse": machine.can_user_use(request.user),
        "machine": machine.pk,
        "canIgnoreRules": any(quota.ignore_rules and quota.can_make_more_reservations(request.user) for quota in
                              Quota.get_user_quotas(request.user, machine.machine_type)),
        "rules": [
            {
                "max_inside": rule.max_hours,
                "max_crossed": rule.max_inside_border_crossed,
                "periods": [
                    [
                        day + rule.start_time.hour / 24 + rule.start_time.minute / 1440,
                        (day + rule.days_changed + rule.end_time.hour / 24 + rule.end_time.minute / 1440) % 7
                    ]
                    for day, _ in enumerate(bin(rule.start_days)[2:][::-1]) if _ == "1"
                ],
            } for rule in ReservationRule.objects.filter(machine_type=machine.machine_type)
        ],
        "reservations": [
            wrap_reservation(reservation, request.user) for reservation in
            Reservation.objects.filter(machine=machine, end_time__gte=start_of_week,
                                       start_time__lt=start_of_week + timezone.timedelta(days=7))
        ]
    }

    return JsonResponse(data)
