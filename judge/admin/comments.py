from django.conf import settings
from django.forms import ModelForm
from django.utils.html import format_html
from django.utils.translation import ungettext, ugettext_lazy as _
from martor.widgets import AdminMartorWidget
from reversion.admin import VersionAdmin
from suit import apps

from judge.models import Comment
from judge.widgets import HeavySelect2Widget

ACE_BASE_URL = getattr(settings, 'ACE_BASE_URL', '//cdnjs.cloudflare.com/ajax/libs/ace/1.1.3/')
HIGHLIGHT_BASE_URL = getattr(settings, 'HIGHLIGHT_BASE_URL', '//cdn.bootcss.com/highlight.js/9.12.0/')
MATHJAX_URL = getattr(settings, 'MATHJAX_URL', '//cdn.bootcss.com/mathjax/2.7.4/MathJax.js')


class CommentForm(ModelForm):
    class Meta:
        widgets = {
            'author': HeavySelect2Widget(data_view='profile_select2'),
            'parent': HeavySelect2Widget(data_view='comment_select2'),
            'body': AdminMartorWidget(),
        }


class CommentAdmin(VersionAdmin):
    fieldsets = (
        (None, {'fields': ('author', 'page', 'parent', 'score', 'hidden')}),
        ('Content', {'fields': ('title', 'body')}),
    )
    list_display = ['author', 'linked_page', 'time']
    search_fields = ['author__user__username', 'author__name', 'page', 'title', 'body']
    actions = ['hide_comment', 'unhide_comment']
    list_filter = ['hidden']
    actions_on_top = True
    actions_on_bottom = True
    form = CommentForm
    date_hierarchy = 'time'

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

    def get_queryset(self, request):
        return Comment.objects.order_by('-time')

    def hide_comment(self, request, queryset):
        count = queryset.update(hidden=True)
        self.message_user(request, ungettext('%d comment successfully hidden.',
                                             '%d comments successfully hidden.',
                                             count) % count)

    hide_comment.short_description = _('Hide comments')

    def unhide_comment(self, request, queryset):
        count = queryset.update(hidden=False)
        self.message_user(request, ungettext('%d comment successfully unhidden.',
                                             '%d comments successfully unhidden.',
                                             count) % count)

    unhide_comment.short_description = _('Unhide comments')

    def linked_page(self, obj):
        link = obj.link
        if link is not None:
            return format_html('<a href="{0}">{1}</a>', link, obj.page)
        else:
            return format_html('{0}', obj.page)

    linked_page.short_description = _('Associated page')
    linked_page.allow_tags = True
    linked_page.admin_order_field = 'page'

    def save_model(self, request, obj, form, change):
        super(CommentAdmin, self).save_model(request, obj, form, change)
        if obj.hidden:
            obj.get_descendants().update(hidden=obj.hidden)
