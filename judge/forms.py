from operator import attrgetter

from django import forms
from django.conf import settings
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.forms import ModelForm, CharField, TextInput
from django.utils.translation import ugettext_lazy as _
from martor.widgets import MartorWidget

from django_ace import AceWidget
from judge.models import Organization, Profile, Submission, PrivateMessage, Language
from judge.utils.subscription import newsletter_id
from judge.widgets import Select2Widget, Select2MultipleWidget

ACE_BASE_URL = getattr(settings, 'ACE_BASE_URL', '//cdnjs.cloudflare.com/ajax/libs/ace/1.1.3/')
HIGHLIGHT_BASE_URL = getattr(settings, 'HIGHLIGHT_BASE_URL', '//cdn.bootcss.com/highlight.js/9.12.0/')


def fix_unicode(string, unsafe=tuple(u'\u202a\u202b\u202d\u202e')):
    return string + (sum(k in unsafe for k in string) - string.count(u'\u202c')) * u'\u202c'


class ProfileForm(ModelForm):
    if newsletter_id is not None:
        newsletter = forms.BooleanField(label=_('Subscribe to contest updates'), initial=False, required=False)
    test_site = forms.BooleanField(label=_('Enable experimental features'), initial=False, required=False)

    class Meta:
        model = Profile
        fields = ['name', 'about', 'organizations', 'timezone', 'language', 'ace_theme', 'user_script', 'math_engine']
        widgets = {
            'name': TextInput(attrs={'style': 'width:100%; box-sizing:border-box'}),
            'user_script': AceWidget(theme='github'),
            'timezone': Select2Widget(attrs={'style': 'width:100%'}),
            'language': Select2Widget(attrs={'style': 'width:100%'}),
            'ace_theme': Select2Widget(attrs={'style': 'width:100%'}),
            'math_engine': Select2Widget(attrs={'style': 'width:100%'}),
            'about': MartorWidget,
            'organizations': Select2MultipleWidget(attrs={'style': 'width:100%'}),
        }

    class Media:
        js = (
            ACE_BASE_URL + 'ace.js',
            ACE_BASE_URL + 'ext-language_tools.js',
            ACE_BASE_URL + 'mode-markdown.js',
            ACE_BASE_URL + 'theme-github.js',
            HIGHLIGHT_BASE_URL + 'highlight.min.js',
        )

    def clean(self):
        organizations = self.cleaned_data.get('organizations') or []
        max_orgs = getattr(settings, 'MAX_USER_ORGANIZATION_COUNT', 3)

        if sum(org.is_open for org in organizations) > max_orgs:
            raise ValidationError(
                _('You may not be part of more than {count} public organizations.').format(count=max_orgs))

        return self.cleaned_data

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(ProfileForm, self).__init__(*args, **kwargs)
        if not user.has_perm('judge.edit_all_organization'):
            self.fields['organizations'].queryset = Organization.objects.filter(
                Q(is_open=True) | Q(id__in=user.profile.organizations.all())
            )

    def clean_name(self):
        return fix_unicode(self.cleaned_data['name'] or '')


class ProblemSubmitForm(ModelForm):
    source = CharField(max_length=65536, widget=AceWidget(theme='twilight', no_ace_media=True))

    def __init__(self, *args, **kwargs):
        super(ProblemSubmitForm, self).__init__(*args, **kwargs)
        self.fields['problem'].empty_label = None
        self.fields['problem'].widget = forms.HiddenInput()
        self.fields['language'].empty_label = None
        self.fields['language'].label_from_instance = attrgetter('display_name')
        self.fields['language'].queryset = Language.objects.filter(judges__online=True).distinct()

    class Meta:
        model = Submission
        fields = ['problem', 'source', 'language']


class EditOrganizationForm(ModelForm):
    class Meta:
        model = Organization
        fields = ['about', 'admins']
        widgets = {'admins': Select2MultipleWidget(),
                   'about': MartorWidget,
                   }

    class Media:
        js = (
            ACE_BASE_URL + 'ace.js',
            ACE_BASE_URL + 'ext-language_tools.js',
            ACE_BASE_URL + 'mode-markdown.js',
            ACE_BASE_URL + 'theme-github.js',
            HIGHLIGHT_BASE_URL + 'highlight.min.js',

        )


class NewMessageForm(ModelForm):
    class Meta:
        model = PrivateMessage
        fields = ['title', 'content']
        widgets = {'content': MartorWidget}


class NewOrganizationForm(EditOrganizationForm):
    class Meta(EditOrganizationForm.Meta):
        fields = ['key'] + EditOrganizationForm.Meta.fields
