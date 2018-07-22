from django.conf import settings
from django.contrib import admin
from django.forms import ModelForm
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _, ugettext, ungettext
from martor.widgets import AdminMartorWidget
from reversion.admin import VersionAdmin
from suit import apps

from django_ace import AceWidget
from judge.models import Profile
from judge.widgets import Select2Widget

ACE_BASE_URL = getattr(settings, 'ACE_BASE_URL', '//cdnjs.cloudflare.com/ajax/libs/ace/1.1.3/')
HIGHLIGHT_BASE_URL = getattr(settings, 'HIGHLIGHT_BASE_URL', '//cdn.bootcss.com/highlight.js/9.12.0/')
MATHJAX_URL = getattr(settings, 'MATHJAX_URL', '//cdn.bootcss.com/mathjax/2.7.4/MathJax.js')


class ProfileForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(ProfileForm, self).__init__(*args, **kwargs)
        self.fields['current_contest'].queryset = self.instance.contest_history.select_related('contest') \
            .only('contest__name', 'user_id', 'virtual')
        self.fields['current_contest'].label_from_instance = \
            lambda obj: '%s v%d' % (obj.contest.name, obj.virtual) if obj.virtual else obj.contest.name

    class Meta:
        widgets = {
            'timezone': Select2Widget,
            'language': Select2Widget,
            'ace_theme': Select2Widget,
            'current_contest': Select2Widget,
            'about': AdminMartorWidget,
        }


class TimezoneFilter(admin.SimpleListFilter):
    title = _('timezone')
    parameter_name = 'timezone'

    def lookups(self, request, model_admin):
        return Profile.objects.values_list('timezone', 'timezone').distinct().order_by('timezone')

    def queryset(self, request, queryset):
        if self.value() is None:
            return queryset
        return queryset.filter(timezone=self.value())


class ProfileAdmin(VersionAdmin):
    fields = ('user', 'name', 'display_rank', 'about', 'organizations', 'timezone', 'language', 'ace_theme',
              'math_engine', 'last_access', 'ip', 'mute', 'user_script', 'current_contest')
    readonly_fields = ('user',)
    list_display = ('admin_user_admin', 'email', 'timezone_full', 'date_joined', 'last_access', 'ip', 'show_public')
    ordering = ('user__username',)
    search_fields = ('user__username', 'name', 'ip', 'user__email')
    list_filter = ('language', TimezoneFilter)
    actions = ('recalculate_points',)
    actions_on_top = True
    actions_on_bottom = True
    form = ProfileForm

    suit_form_size = {
        'fields': {
            'about': apps.SUIT_FORM_SIZE_FULL,
        },
        'widgets': {
            'AdminMartorWidget': apps.SUIT_FORM_SIZE_FULL,
            'AceWidget': apps.SUIT_FORM_SIZE_INLINE
        },
    }

    class Media:
        js = (
            ACE_BASE_URL + 'ace.js',
            ACE_BASE_URL + 'ext-language_tools.js',
            ACE_BASE_URL + 'mode-markdown.js',
            ACE_BASE_URL + 'theme-github.js',
            HIGHLIGHT_BASE_URL + 'highlight.min.js',
            MATHJAX_URL,
        )

    def show_public(self, obj):
        return format_html(u'<a href="{0}" style="white-space:nowrap;">{1}</a>',
                           obj.get_absolute_url(), ugettext('View on site'))

    show_public.short_description = ''

    def admin_user_admin(self, obj):
        return obj.long_display_name

    admin_user_admin.admin_order_field = 'user__username'
    admin_user_admin.short_description = _('User')

    def email(self, obj):
        return obj.user.email

    email.admin_order_field = 'user__email'
    email.short_description = _('Email')

    def timezone_full(self, obj):
        return obj.timezone

    timezone_full.admin_order_field = 'timezone'
    timezone_full.short_description = _('Timezone')

    def date_joined(self, obj):
        return obj.user.date_joined

    date_joined.admin_order_field = 'user__date_joined'
    date_joined.short_description = _('date joined')

    def recalculate_points(self, request, queryset):
        count = 0
        for profile in queryset:
            profile.calculate_points()
            count += 1
        self.message_user(request, ungettext('%d user have scores recalculated.',
                                             '%d users have scores recalculated.',
                                             count) % count)

    recalculate_points.short_description = _('Recalculate scores')

    def get_form(self, request, obj=None, **kwargs):
        form = super(ProfileAdmin, self).get_form(request, obj, **kwargs)
        form.base_fields['user_script'].widget = AceWidget('javascript', request.user.profile.ace_theme)
        return form
