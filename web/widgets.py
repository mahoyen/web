import django.forms as forms
from django.utils.translation import gettext_lazy as _


class SemanticTimeInput(forms.TimeInput):
    template_name = "web/forms/widgets/semantic_time.html"


class SemanticChoiceInput(forms.Select):
    template_name = "web/forms/widgets/semantic_select.html"


class SemanticSearchableChoiceInput(forms.Select):
    template_name = "web/forms/widgets/semantic_search_select.html"
    prompt_text = _("Choose value")

    def __init__(self, *args, **kwargs):
        super().__init__()
        self.attrs["prompt_text"] = kwargs.pop("prompt_text", self.prompt_text)
        self.attrs["force_selection"] = kwargs.pop("force_selection", False)


class SemanticDateInput(forms.DateInput):
    template_name = "web/forms/widgets/semantic_date.html"
    # TODO: FIX Media


class SemanticDateTimeInput(forms.DateTimeInput):
    template_name = "web/forms/widgets/semantic_date_time.html"

    class Media:
        js = ("web/calendar/calendar.min.js", "web/js/widgets/calendar.js")
        css = {
            "all": (
                "web/calendar/calendar.min.css",
            )
        }

    def __init__(self, *args, **kwargs):
        super().__init__()
        self.attrs["default"] = kwargs.pop("default", None)
        self.attrs["custom_js"] = kwargs.pop("custom_js", False)


class SemanticLabeledCheckboxInput(forms.CheckboxInput):
    template_name = "web/forms/widgets/semantic_labeled_checkbox.html"

    def __init__(self, *args, **kwargs):
        super().__init__()
        self.attrs["label"] = kwargs.pop("label", "")


class SemanticGroupedChoiceInput(forms.Select):
    template_name = "web/forms/widgets/semantic_grouped_select.html"

    def __init__(self, *args, **kwargs):
        super().__init__(attrs=kwargs.pop("attrs"))
        self.attrs["label"] = kwargs.pop("label", "")
        self.attrs["group_label"] = kwargs.pop("group_label", "")
        self.attrs["prompt"] = kwargs.pop("prompt", _("Select"))
        self.attrs["group_prompt"] = kwargs.pop("group_prompt", _("Select"))

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        group_value = ""
        for group in self.choices:
            for element in group[1]:
                # Must check for string, since invalid forms have string values
                if isinstance(value, str) and str(element[0]) == value or element[0] == value:
                    group_value = group[0]

        context["widget"].update({
            "group_value": group_value
        })
        return context
