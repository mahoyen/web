import math
from datetime import timedelta

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.http import HttpResponseRedirect, JsonResponse, Http404
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.translation import get_language
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.generic import UpdateView, CreateView, TemplateView, DeleteView, DetailView, RedirectView

from mail import email
from news.forms import EventForm
from news.forms import TimePlaceForm, EventRegistrationForm, ArticleForm
from news.models import Article, Event, TimePlace, EventTicket
from web import settings
from web.templatetags.permission_tags import has_any_article_permission, has_any_event_permission


class ViewEventsView(TemplateView):
    template_name = 'news/events.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        past, future = [], []
        for event in Event.objects.filter(hidden=False):
            if event.private and not self.request.user.has_perm('news.can_view_private'):
                continue
            if not event.get_future_occurrences().exists() and not event.get_past_occurrences().exists():
                continue
            if event.standalone:
                if event.get_future_occurrences().exists():
                    future.append({
                        "first_occurrence": event.get_future_occurrences().first(),
                        "event": event,
                        "number_of_occurrences": event.timeplace_set.count(),
                    })
                else:
                    past.append({
                        "last_occurrence": event.get_past_occurrences().first(),
                        "event": event,
                        "number_of_occurrences": event.timeplace_set.count(),
                    })
            else:
                for occurrence in event.get_future_occurrences():
                    future.append({
                        "first_occurrence": occurrence,
                        "event": event,
                        "number_of_occurrences": 1,
                    })
                if event.get_past_occurrences().exists():
                    past.append({
                        "last_occurrence": event.get_past_occurrences().first(),
                        "event": event,
                        "number_of_occurrences": event.get_past_occurrences().count(),
                    })

        context.update({
            'past': sorted(past, key=lambda event: event["last_occurrence"].start_date, reverse=True),
            'future': sorted(future, key=lambda event: event["first_occurrence"].start_date),
        })
        return context


class ViewArticlesView(TemplateView):
    template_name = 'news/articles.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'articles': Article.objects.published().filter(),
        })
        return context


class ViewEventView(TemplateView):
    template_name = 'news/event.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        event = get_object_or_404(Event, pk=kwargs['pk'])
        context.update({
            'article': event,
            'timeplaces': event.timeplace_set.all() if event.standalone else event.timeplace_set.future(),
        })
        if (event.hidden and not self.request.user.has_perm('news.change_event')) \
                or (event.private and not self.request.user.has_perm('news.can_view_private')):
            raise Http404()
        return context


class ViewArticleView(TemplateView):
    template_name = 'news/article.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        article = get_object_or_404(Article, pk=kwargs['pk'])
        context.update({
            'article': article,
        })
        if (article not in Article.objects.published() and not self.request.user.has_perm('news.change_article')) \
                or (article.private and not self.request.user.has_perm('news.can_view_private')):
            raise Http404()
        return context


class AdminArticleView(TemplateView):
    template_name = 'news/admin_articles.html'

    def get_context_data(self, **kwargs):
        if not has_any_article_permission(self.request.user) and not self.request.user.is_superuser:
            raise Http404()
        context = super().get_context_data(**kwargs)
        context.update({
            'articles': Article.objects.all(),
        })
        return context


class AdminEventsView(TemplateView):
    template_name = 'news/admin_events.html'

    def get_context_data(self, **kwargs):
        if not has_any_event_permission(self.request.user) and not self.request.user.is_superuser:
            raise Http404()
        context = super().get_context_data(**kwargs)
        context.update({
            'events': Event.objects.all(),
        })
        return context


class AdminEventView(DetailView):
    template_name = 'news/admin_event.html'
    model = Event


class EditArticleView(PermissionRequiredMixin, UpdateView):
    model = Article
    template_name = 'news/article_edit.html'
    form_class = ArticleForm

    permission_required = (
        'news.change_article',
    )

    def get_success_url(self):
        return reverse_lazy("admin-articles")


class CreateArticleView(PermissionRequiredMixin, CreateView):
    model = Article
    template_name = 'news/article_create.html'
    form_class = ArticleForm
    permission_required = (
        'news.add_article',
    )

    def get_success_url(self):
        return reverse_lazy("admin-articles")


class EditEventView(PermissionRequiredMixin, UpdateView):
    model = Event
    template_name = 'news/event_edit.html'
    form_class = EventForm
    permission_required = (
        'news.change_event',
    )

    def get_success_url(self):
        return reverse_lazy("admin-event", args=(self.object.id,))


class CreateEventView(PermissionRequiredMixin, CreateView):
    model = Event
    template_name = 'news/event_create.html'
    form_class = EventForm
    permission_required = (
        'news.add_event',
    )

    def get_success_url(self):
        return reverse_lazy("admin-event", args=(self.object.id,))


class EditTimePlaceView(PermissionRequiredMixin, UpdateView):
    model = TimePlace
    template_name = 'news/timeplace_edit.html'
    form_class = TimePlaceForm
    permission_required = (
        'news.change_timeplace',
    )

    def get_form(self, form_class=None):
        form = self.form_class(**self.get_form_kwargs())
        if self.object.event.standalone:
            del form.fields["number_of_tickets"]
        return form

    def get_success_url(self):
        return reverse_lazy("admin-event", args=(self.object.event.id,))


class DuplicateTimePlaceView(PermissionRequiredMixin, View):
    permission_required = (
        'news.add_timeplace',
    )

    def get(self, request, pk):
        timeplace = get_object_or_404(TimePlace, pk=pk)
        now = timezone.now()
        if now.date() > timeplace.start_date:
            delta_days = (timezone.now().date() - timeplace.start_date).days
            weeks = math.ceil(delta_days / 7)
        else:
            weeks = 1
        timeplace.start_date += timedelta(weeks=weeks)
        if timeplace.end_date:
            timeplace.end_date += timedelta(weeks=weeks)
        timeplace.hidden = True
        timeplace.pk = None
        timeplace.save()
        return HttpResponseRedirect(reverse('timeplace-edit', args=(timeplace.pk,)))


class CreateTimePlaceView(PermissionRequiredMixin, CreateView):
    model = TimePlace
    template_name = "news/timeplace_create.html"
    form_class = TimePlaceForm
    permission_required = (
        'news.add_timeplace',
    )

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        event = get_object_or_404(Event, pk=self.kwargs["event_pk"])
        form.fields["event"].initial = event.pk
        return form

    def get_success_url(self):
        return reverse_lazy("admin-event", args=(self.object.event.id,))


class AdminArticleToggleView(PermissionRequiredMixin, View):
    model = Article
    permission_required = (
        'news.change_article',
    )

    def post(self, request):
        pk, toggle = request.POST.get('pk'), request.POST.get('toggle')
        try:
            object = self.model.objects.get(pk=pk)
            val = not getattr(object, toggle)
            setattr(object, toggle, val)
            object.save()
            color = 'yellow' if val else 'grey'
        except (self.model.DoesNotExist, AttributeError):
            return JsonResponse({})

        return JsonResponse({
            'color': color,
        })


class AdminEventToggleView(AdminArticleToggleView):
    model = Event
    permission_required = (
        'news.change_event',
    )


class AdminTimeplaceToggleView(AdminArticleToggleView):
    model = TimePlace
    permission_required = (
        'news.change_timeplace',
    )


class DeleteArticleView(PermissionRequiredMixin, DeleteView):
    model = Article
    success_url = reverse_lazy('admin-articles')
    permission_required = (
        'news.delete_article',
    )


class DeleteEventView(PermissionRequiredMixin, DeleteView):
    model = Event
    success_url = reverse_lazy('admin-events')
    permission_required = (
        'news.delete_event',
    )


class DeleteTimePlaceView(PermissionRequiredMixin, DeleteView):
    model = TimePlace
    permission_required = (
        'news.delete_timeplace',
    )

    def get_success_url(self):
        return reverse_lazy("admin-event", args=(self.object.event.id,))


class EventRegistrationView(CreateView):
    model = EventTicket
    template_name = "news/event_registration.html"
    form_class = EventRegistrationForm

    @property
    def timeplace(self):
        if "timeplace_pk" in self.kwargs:
            return get_object_or_404(TimePlace, pk=self.kwargs["timeplace_pk"])
        return None

    @property
    def event(self):
        if "event_pk" in self.kwargs:
            return get_object_or_404(Event, pk=self.kwargs["event_pk"])
        return None

    def is_registration_allowed(self):
        return self.timeplace and self.timeplace.can_register(self.request.user) \
               or self.event and self.event.can_register(self.request.user)

    def form_valid(self, form):
        if not self.is_registration_allowed():
            form.add_error(None, _("Could not register you for the event, please try again later."))
            return self.form_invalid(form)

        ticket = form.save()
        if self.request.user.is_authenticated:
            ticket.user = self.request.user

        ticket.event = self.event
        ticket.timeplace = self.timeplace
        ticket.save()

        async_to_sync(get_channel_layer().send)(
            "email", {
                "type": "send_html",
                "html_render": email.render_html({"ticket": ticket}, "email/ticket.html"),
                "text": email.render_text({"ticket": ticket}, text_template_name="email/ticket.txt"),
                "subject": gettext("Your ticket!"),
                "from": settings.EVENT_TICKET_EMAIL,
                "to": ticket.email,
            }
        )

        self.object = ticket
        return HttpResponseRedirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data.update({
            "timeplace": self.timeplace,
            "event": self.event,
        })
        return context_data

    def get_success_url(self):
        return reverse_lazy("ticket", args=(self.object.uuid,))

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if self.request.user.is_authenticated:
            kwargs["initial"].update({
                "name": self.request.user.get_full_name(),
                "email": self.request.user.email,
            })
        kwargs["initial"].update({
            "language": get_language()
        })
        return kwargs


class TicketView(DetailView):
    model = EventTicket
    template_name = "news/ticket_overview.html"

    def get_context_data(self, **kwargs):
        return super().get_context_data(**kwargs)


class MyTicketsView(TemplateView):
    template_name = "news/my_tickets.html"

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data.update({
            "tickets": EventTicket.objects.filter(user=self.request.user),
        })
        return context_data


class ClaimTicketView(RedirectView):
    permanent = False
    query_string = True
    pattern_name = "ticket"

    def get_redirect_url(self, *args, **kwargs):
        ticket = get_object_or_404(EventTicket, pk=kwargs.get("pk", 0), user=None)
        ticket.user = self.request.user
        ticket.save()
        return super().get_redirect_url(*args, **kwargs)


class AdminEventTicketView(TemplateView):
    template_name = "news/admin_event_tickets.html"

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data()
        event = get_object_or_404(Event, pk=kwargs.pop("pk", 0))
        if not event.number_of_tickets:
            raise Http404()
        context_data.update({
            "tickets": event.eventticket_set.order_by("-active").all(),
            "object": event,
            "event": event,
        })
        return context_data


class AdminTimeplaceTicketView(TemplateView):
    template_name = "news/admin_event_tickets.html"

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data()
        timeplace = get_object_or_404(TimePlace, pk=kwargs.pop("pk", 0))
        if not timeplace.number_of_tickets:
            raise Http404()
        context_data.update({
            "tickets": timeplace.eventticket_set.order_by("-active").all(),
            "event": timeplace.event,
            "object": timeplace
        })
        return context_data


class CancelTicketView(RedirectView):
    permanent = False
    query_string = True
    pattern_name = "ticket"

    def get_redirect_url(self, *args, **kwargs):
        ticket = get_object_or_404(EventTicket, pk=kwargs.get("pk", 0))

        # Allow for toggling if a ticket is canceled or not
        if self.request.user.has_perm("news.cancel_ticket"):
            ticket.active = not ticket.active
        elif self.request.user == ticket.user or ticket.user is None:
            ticket.active = False
        ticket.save()

        next_page = self.request.GET.get("next")
        if next_page is None:
            return super().get_redirect_url(*args, **kwargs)
        return next_page
