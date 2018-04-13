from django.conf.urls import url, include
from django.contrib import admin
from django.contrib.auth.decorators import login_required

from checkin.views import CheckInView, ShowSkillsView, ProfilePageView, SuggestSkillView, CreateProfileView

urlpatterns = [
    url(r'^$', ShowSkillsView.as_view()),
    url(r'^profile$', login_required(ProfilePageView.as_view()), name="profile"),
    url(r'^profile/create$', login_required(CreateProfileView.as_view()), name="create_profile"),
    url(r'^post/$', CheckInView.as_view()),
    url(r'^suggest/$', login_required(SuggestSkillView.as_view()), name="suggest"),
]