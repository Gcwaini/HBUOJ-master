from django.conf import settings
from django.contrib.admin import ModelAdmin
from django.contrib.admin.options import StackedInline
from django.forms import ModelForm
from martor.widgets import AdminMartorWidget
from suit import apps

from judge.models import TicketMessage
from judge.widgets import HeavySelect2Widget, HeavySelect2MultipleWidget

ACE_BASE_URL = getattr(settings, 'ACE_BASE_URL', '//cdnjs.cloudflare.com/ajax/libs/ace/1.1.3/')
HIGHLIGHT_BASE_URL = getattr(settings, 'HIGHLIGHT_BASE_URL', '//cdn.bootcss.com/highlight.js/9.12.0/')
MATHJAX_URL = getattr(settings, 'MATHJAX_URL', '//cdn.bootcss.com/mathjax/2.7.4/MathJax.js')


class TicketMessageForm(ModelForm):
    class Meta:
        widgets = {
            'user': HeavySelect2Widget(data_view='profile_select2', attrs={'style': 'width: 100%'}),
            'body': AdminMartorWidget,
        }


class TicketMessageInline(StackedInline):
    model = TicketMessage
    form = TicketMessageForm
    fields = ('user', 'body')
    extra = 1

    suit_form_size = {
        'fields': {
            'body': apps.SUIT_FORM_SIZE_FULL
        },
    }


class TicketForm(ModelForm):
    class Meta:
        widgets = {
            'user': HeavySelect2Widget(data_view='profile_select2', attrs={'style': 'width: 100%'}),
            'assignees': HeavySelect2MultipleWidget(data_view='profile_select2', attrs={'style': 'width: 100%'}),
        }


class TicketAdmin(ModelAdmin):
    fields = ('title', 'time', 'user', 'assignees', 'content_type', 'object_id', 'notes')
    readonly_fields = ('time',)
    list_display = ('title', 'user', 'time', 'linked_item')
    inlines = [TicketMessageInline]
    form = TicketForm
    date_hierarchy = 'time'

    class Media:
        js = (
            ACE_BASE_URL + 'ace.js',
            ACE_BASE_URL + 'ext-language_tools.js',
            ACE_BASE_URL + 'mode-markdown.js',
            ACE_BASE_URL + 'theme-github.js',
            HIGHLIGHT_BASE_URL + 'highlight.min.js',
            MATHJAX_URL,
        )
