from allauth.account.forms import SignupForm
from django import forms
from django.conf import settings
from django.forms import CharField, ChoiceField, ModelChoiceField
from django.utils.translation import ugettext_lazy as _
from sortedm2m.forms import SortedMultipleChoiceField

from judge.models import Profile, Language, Organization, TIMEZONE
from judge.utils.recaptcha import ReCaptchaWidget, ReCaptchaField
from judge.utils.subscription import Subscription, newsletter_id
from judge.widgets import Select2Widget, Select2MultipleWidget


class MySignupForm(SignupForm):
    username = forms.RegexField(regex=r'^\w+$', max_length=30, label=_('Username'),
                                error_messages={'invalid': _('A username must contain letters, '
                                                             'numbers, or underscores')})
    display_name = CharField(max_length=50, required=False, label=_('Real name (optional)'))
    timezone = ChoiceField(label=_('Timezone'), choices=TIMEZONE,
                           widget=Select2Widget(attrs={'style': 'width:100%'}),
                           initial=getattr(settings,
                                           'DEFAULT_USER_TIME_ZONE',
                                           'Asia/Shanghai'))
    language = ModelChoiceField(queryset=Language.objects.all(),
                                label=_('Preferred language'),
                                empty_label=None,
                                widget=Select2Widget(attrs={'style': 'width:100%'}),
                                initial=Language.objects.get(
                                    key=getattr(settings,
                                                'DEFAULT_USER_LANGUAGE',
                                                'CPP11')))
    organizations = SortedMultipleChoiceField(queryset=Organization.objects.filter(is_open=True),
                                              label=_('Organizations'),
                                              required=False,
                                              widget=Select2MultipleWidget(attrs={'style': 'width:100%'}))

    if newsletter_id is not None:
        newsletter = forms.BooleanField(label=_('Subscribe to newsletter?'), initial=True, required=False)

    if ReCaptchaField is not None:
        captcha = ReCaptchaField(widget=ReCaptchaWidget())

    def save(self, request):
        user = super(MySignupForm, self).save(request)
        profile, _ = Profile.objects.get_or_create(user=user, defaults={
            'language': Language.get_python2()
        })

        profile.name = self.cleaned_data.get('display_name')
        profile.timezone = self.cleaned_data.get('timezone')
        profile.language = self.cleaned_data.get('language')
        profile.organizations.add(*self.cleaned_data.get('organizations'))
        profile.save()

        if newsletter_id is not None and self.cleaned_data.get('newsletter'):
            Subscription(user=user, newsletter_id=newsletter_id, subscribed=True).save()
        return user
