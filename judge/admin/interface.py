from django.conf import settings
from django.contrib import admin
from django.forms import ModelForm
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _
from martor.widgets import AdminMartorWidget
from mptt.admin import DraggableMPTTAdmin
from reversion.admin import VersionAdmin
from suit import apps

from judge.dblock import LockModel
from judge.models import NavigationBar
from judge.widgets import HeavySelect2MultipleWidget, HeavySelect2Widget

ACE_BASE_URL = getattr(settings, 'ACE_BASE_URL', '//cdnjs.cloudflare.com/ajax/libs/ace/1.1.3/')
HIGHLIGHT_BASE_URL = getattr(settings, 'HIGHLIGHT_BASE_URL', '//cdn.bootcss.com/highlight.js/9.12.0/')
MATHJAX_URL = getattr(settings, 'MATHJAX_URL', '//cdn.bootcss.com/mathjax/2.7.4/MathJax.js')


class NavigationBarAdmin(DraggableMPTTAdmin):
    list_display = DraggableMPTTAdmin.list_display + ('key', 'linked_path')
    fields = ('key', 'label', 'path', 'order', 'regex', 'parent')
    list_editable = ()  # Bug in SortableModelAdmin: 500 without list_editable being set
    mptt_level_indent = 20
    sortable = 'order'

    def __init__(self, *args, **kwargs):
        super(NavigationBarAdmin, self).__init__(*args, **kwargs)
        self.__save_model_calls = 0

    def linked_path(self, obj):
        return format_html(u'<a href="{0}" target="_blank">{0}</a>', obj.path)

    linked_path.short_description = _('link path')

    def save_model(self, request, obj, form, change):
        self.__save_model_calls += 1
        return super(NavigationBarAdmin, self).save_model(request, obj, form, change)

    def changelist_view(self, request, extra_context=None, **kwargs):
        self.__save_model_calls = 0
        with NavigationBar.objects.disable_mptt_updates():
            result = super(NavigationBarAdmin, self).changelist_view(request, extra_context)
        if self.__save_model_calls:
            with LockModel(write=(NavigationBar,)):
                NavigationBar.objects.rebuild()
        return result


class BlogPostForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(BlogPostForm, self).__init__(*args, **kwargs)
        self.fields['authors'].widget.can_add_related = False

    class Meta:
        widgets = {
            'authors': HeavySelect2MultipleWidget(data_view='profile_select2', attrs={'style': 'width: 100%'}),
            'content': AdminMartorWidget,
            'summary': AdminMartorWidget,
        }


class BlogPostAdmin(VersionAdmin):
    fieldsets = (
        (None, {'fields': ('title', 'slug', 'authors', 'visible', 'sticky', 'publish_on')}),
        (_('Content'), {'fields': ('content', 'og_image',)}),
        (_('Summary'), {'classes': ('collapse',), 'fields': ('summary',)}),
    )
    prepopulated_fields = {'slug': ('title',)}
    list_display = ('id', 'title', 'visible', 'sticky', 'publish_on')
    list_display_links = ('id', 'title')
    ordering = ('-publish_on',)
    form = BlogPostForm
    date_hierarchy = 'publish_on'

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

    def has_change_permission(self, request, obj=None):
        return (request.user.has_perm('judge.edit_all_post') or
                request.user.has_perm('judge.change_blogpost') and (
                        obj is None or
                        obj.authors.filter(id=request.user.profile.id).exists()))


class SolutionForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(SolutionForm, self).__init__(*args, **kwargs)
        self.fields['authors'].widget.can_add_related = False

    class Meta:
        widgets = {
            'authors': HeavySelect2MultipleWidget(data_view='profile_select2', attrs={'style': 'width: 100%'}),
            'problem': HeavySelect2Widget(data_view='problem_select2', attrs={'style': 'width: 250px'}),
            'content': AdminMartorWidget,
        }


class LicenseForm(ModelForm):
    class Meta:
        widgets = {'text': AdminMartorWidget}


class LicenseAdmin(admin.ModelAdmin):
    fields = ('key', 'link', 'name', 'display', 'icon', 'text')
    list_display = ('name', 'key')
    form = LicenseForm

    suit_form_size = {
        'fields': {
            'text': apps.SUIT_FORM_SIZE_FULL,
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
