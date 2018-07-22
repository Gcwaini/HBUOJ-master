from django.conf import settings
from django.contrib import admin
from django.forms import ModelForm
from django.utils.html import format_html
from django.utils.translation import ugettext, ugettext_lazy as _
from martor.widgets import AdminMartorWidget
from reversion.admin import VersionAdmin
from suit import apps

from judge.models import Organization
from judge.widgets import HeavySelect2MultipleWidget, HeavySelect2Widget

ACE_BASE_URL = getattr(settings, 'ACE_BASE_URL', '//cdnjs.cloudflare.com/ajax/libs/ace/1.1.3/')
HIGHLIGHT_BASE_URL = getattr(settings, 'HIGHLIGHT_BASE_URL', '//cdn.bootcss.com/highlight.js/9.12.0/')
MATHJAX_URL = getattr(settings, 'MATHJAX_URL', '//cdn.bootcss.com/mathjax/2.7.4/MathJax.js')


class OrganizationForm(ModelForm):
    class Meta:
        widgets = {
            'admins': HeavySelect2MultipleWidget(data_view='profile_select2', attrs={'style': 'width: 100%'}),
            'registrant': HeavySelect2Widget(data_view='profile_select2'),
            'about': AdminMartorWidget
        }


class OrganizationAdmin(VersionAdmin):
    readonly_fields = ('creation_date',)
    fields = ('name', 'key', 'short_name', 'is_open', 'about', 'slots', 'registrant', 'creation_date', 'admins')
    list_display = ('name', 'key', 'short_name', 'is_open', 'slots', 'registrant', 'show_public')
    actions_on_top = True
    actions_on_bottom = True
    form = OrganizationForm

    suit_form_size = {
        'widgets': {
            'AdminMartorWidget': apps.SUIT_FORM_SIZE_FULL
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

    def get_readonly_fields(self, request, obj=None):
        fields = self.readonly_fields
        if not request.user.has_perm('judge.organization_admin'):
            return fields + ('registrant', 'admins', 'is_open', 'slots')
        return fields

    def get_queryset(self, request):
        queryset = Organization.objects.all()
        if request.user.has_perm('judge.edit_all_organization'):
            return queryset
        else:
            return queryset.filter(admins=request.user.profile.id)

    def has_change_permission(self, request, obj=None):
        if not request.user.has_perm('judge.change_organization'):
            return False
        if request.user.has_perm('judge.edit_all_organization') or obj is None:
            return True
        return obj.admins.filter(id=request.user.profile.id).exists()


class OrganizationRequestAdmin(admin.ModelAdmin):
    list_display = ('username', 'organization', 'state', 'time')
    readonly_fields = ('user', 'organization')

    def username(self, obj):
        return obj.user.user.username

    username.short_description = _('username')
    username.admin_order_field = 'user__user__username'
