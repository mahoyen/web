from django import forms
from django.contrib.auth.models import User
from django.db.models import Q
from django.forms import ModelChoiceField, IntegerField, ModelForm, BooleanField
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from make_queue.fields import MachineTypeField, MachineTypeForm
from make_queue.models.course import Printer3DCourse
from make_queue.models.models import Machine, ReservationRule, Quota, Reservation
from news.models import TimePlace
from web.widgets import SemanticTimeInput, SemanticChoiceInput, SemanticSearchableChoiceInput, SemanticDateInput, \
    SemanticLabeledCheckboxInput, SemanticGroupedChoiceInput, SemanticDateTimeInput


class ReservationForm(ModelForm):
    class Meta:
        model = Reservation
        fields = ["machine", "start_time", "end_time", "comment", "event", "special", "special_text"]
        widgets = {
            "machine": SemanticGroupedChoiceInput(label=_("Machine"), group_label=_("Machine type"),
                                                  group_prompt=_("Select machine type"), prompt=_("Select machine"),
                                                  attrs={"required": True}),
            "special": SemanticLabeledCheckboxInput(label="MAKE NTNU"),
            "event": SemanticSearchableChoiceInput(prompt_text=_("Select event")),
            "start_time": SemanticDateTimeInput(default=lambda: timezone.now(), custom_js=True),
            "end_time": SemanticDateTimeInput(custom_js=True),
        }

    is_event = BooleanField(widget=SemanticLabeledCheckboxInput(label=_("Event")), required=False)

    def __init__(self, *args, user=None, machine=0, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["is_event"].initial = self.instance is not None and self.instance.event is not None
        # Only show the user the machines it can use
        self.fields["machine"].choices = (
            (machine_type.name, tuple(
                (machine.pk, machine.name) for machine in Machine.objects.filter(machine_type=machine_type)
            )) for machine_type in MachineTypeField.possible_machine_types if machine_type.can_user_use(user)
        )

        self.fields["event"].choices = ((timeplace.pk, str(timeplace)) for timeplace in TimePlace.objects.future())
        # Want to be able to set initial value for the machine field
        if machine:
            self.fields["machine"].initial = machine


class RuleForm(forms.ModelForm):
    day_field_names = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]

    def __init__(self, *args, **kwargs):
        super(RuleForm, self).__init__(*args, **kwargs)
        rule_obj = kwargs["instance"]
        for shift, field_name in enumerate(self.day_field_names):
            self.fields[field_name] = forms.BooleanField(required=False)
            if rule_obj is not None:
                self.fields[field_name].initial = rule_obj.start_days & (1 << shift) > 0

    def clean(self):
        cleaned_data = super().clean()

        rule = ReservationRule(machine_type=cleaned_data["machine_type"], max_hours=0, max_inside_border_crossed=0,
                               start_time=cleaned_data["start_time"], end_time=cleaned_data["end_time"],
                               days_changed=cleaned_data["days_changed"], start_days=self.get_start_days(cleaned_data))

        rule.is_valid_rule(raise_error=True)

        return cleaned_data

    @staticmethod
    def get_start_days(cleaned_data):
        return sum(cleaned_data[field_name] << shift for shift, field_name in enumerate(RuleForm.day_field_names))

    def save(self, commit=True):
        rule = super(RuleForm, self).save(commit=False)
        rule.start_days = self.get_start_days(self.cleaned_data)
        if commit:
            rule.save()
        return rule

    class Meta:
        model = ReservationRule
        fields = ["start_time", "end_time", "days_changed", "max_hours", "max_inside_border_crossed", "machine_type"]
        widgets = {
            "start_time": SemanticTimeInput(),
            "end_time": SemanticTimeInput(),
            "machine_type": SemanticChoiceInput(),
        }


class QuotaForm(forms.ModelForm):
    class UserModelChoiceField(ModelChoiceField):
        def label_from_instance(self, obj):
            return f'{obj.get_full_name()} - {obj.username}'

    user = UserModelChoiceField(queryset=User.objects.all(),
                                widget=SemanticSearchableChoiceInput(prompt_text=_("Select user")),
                                label=_("User"),
                                required=False)

    def clean(self):
        cleaned_data = super().clean()
        user = cleaned_data["user"]
        all_users = cleaned_data["all"]
        if user is None and not all_users:
            raise ValueError("User cannot be None when the quota is not for all users")
        if user is not None and all_users:
            raise ValueError("User cannot be set when the all users is set")
        return cleaned_data

    class Meta:
        model = Quota
        exclude = []


class Printer3DCourseForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(**kwargs)
        self.fields["user"] = ModelChoiceField(
            queryset=User.objects.filter(Q(printer3dcourse=None) | Q(printer3dcourse=self.instance)),
            required=False, widget=SemanticSearchableChoiceInput(prompt_text=_("Select user")),
            label=Printer3DCourse._meta.get_field('user').verbose_name)
        self.fields["card_number"].required = False

    class Meta:
        model = Printer3DCourse
        exclude = []
        widgets = {
            "status": SemanticChoiceInput(),
            "date": SemanticDateInput(),
            "username": forms.TextInput(attrs={"autofocus": "autofocus"}),
        }


class FreeSlotForm(forms.Form):
    machine_type = MachineTypeForm(
        choices=((machine_type.id, machine_type.name) for machine_type in MachineTypeField.possible_machine_types),
        initial=1, label=_("Machine type"))
    hours = IntegerField(min_value=0, initial=1, label=_("Duration in hours"))
    minutes = IntegerField(min_value=0, max_value=59, initial=0, label=_("Duration in minutes"))
