from django.conf.urls.i18n import i18n_patterns
from django.contrib.auth.decorators import permission_required
from django.urls import path, include
from django.views.generic import TemplateView
from django_hosts import reverse

from internal.views import MembersListView, AddMemberView, EditMemberView, MemberUndoQuitView, MemberQuitView, \
    MemberUndoRetireView, MemberRetireView, ToggleSystemAccessView
from web.url_util import decorated_includes

unsafe_urlpatterns = [
    path("members", MembersListView.as_view(), name="members"),
    path("members/<int:pk>", MembersListView.as_view(), name="members"),
    path("members/add", AddMemberView.as_view(), name="add-member"),
    path("members/<int:pk>/edit", EditMemberView.as_view(), name="edit-member"),
    path("members/<int:pk>/quit", permission_required("internal.can_edit_group_membership")(MemberQuitView.as_view()), name="member-quit"),
    path("members/<int:pk>/quit/undo", permission_required("internal.can_edit_group_membership")(MemberUndoQuitView.as_view()), name="member-undo-quit"),
    path("members/<int:pk>/retire", permission_required("internal.can_edit_group_membership")(MemberRetireView.as_view()), name="member-retire"),
    path("members/<int:pk>/retire/undo", permission_required("internal.can_edit_group_membership")(MemberUndoRetireView.as_view()), name="member-undo-retire"),
    path("members/access/<int:pk>/change", ToggleSystemAccessView.as_view(), name="toggle-system-access"),
    # TODO: Change to the HomeView when there is actually some content to show there
    path("", MembersListView.as_view(), name="home"),
]

urlpatterns = [
    path('robots.txt', TemplateView.as_view(template_name='internal/robots.txt', content_type='text/plain')),
    path("i18n/", decorated_includes(
        permission_required("internal.is_internal", login_url=reverse("login", host="main")),
        include("django.conf.urls.i18n")
    )),
]

urlpatterns += i18n_patterns(
    path("", decorated_includes(
        permission_required("internal.is_internal", login_url=reverse("login", host="main")),
        include(unsafe_urlpatterns)
    )),
    prefix_default_language=False
)
