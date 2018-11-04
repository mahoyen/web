from datetime import datetime

from django.urls import reverse
from django_ical.views import ICalFeed

from web import settings
from .models import TimePlace


class EventFeed(ICalFeed):
    """An iCal feed of all the events available to the user"""
    file_name = 'events.ics'

    def get_object(self, request, *args, **kwargs):
        return {
            'user_can_view_private': request.user.has_perm('news.can_view_private'),
            'query_kwargs': {},
        }

    def items(self, attrs):
        items = TimePlace.objects.all()

        if attrs['query_kwargs']:
            items = items.filter(**attrs['query_kwargs'])

        if not attrs['user_can_view_private']:
            items = items.filter(event__private=False)

        return items

    def item_link(self, item):
        return reverse('event', kwargs={'pk': item.pk})

    def item_title(self, item):
        return item.event.title

    def item_description(self, item):
        return item.event.clickbait

    def item_start_datetime(self, item):
        return datetime.combine(item.start_date, item.start_time)

    def item_end_datetime(self, item):
        date = item.end_date if item.end_date else item.start_date
        return datetime.combine(date, item.end_time)

    def item_location(self, item):
        return item.place


class SingleEventFeed(EventFeed):
    """An iCal feed of all occurences of a single event"""
    def file_name(self, attrs):
        title = self.items(attrs).values_list('event__title', flat=True).first()
        return f'{title}.ics'

    def get_object(self, request, *args, **kwargs):
        attrs = super().get_object(request, *args, **kwargs)
        attrs['query_kwargs']['event_id'] = int(kwargs['pk'])

        return attrs


class SingleTimePlaceFeed(EventFeed):
    """An iCal feed of a single occurences of an event"""

    def file_name(self, attrs):
        title = self.items(attrs).values_list('event__title', flat=True).first()
        return f'{title}.ics'

    def get_object(self, request, *args, **kwargs):
        attrs = super().get_object(request, *args, **kwargs)
        attrs['query_kwargs']['id'] = int(kwargs['pk'])

        return attrs
