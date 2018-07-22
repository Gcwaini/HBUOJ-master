from django import forms
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db.models import Count
from django.db.models.expressions import Value, F
from django.db.models.functions import Coalesce
from django.forms import ModelForm
from django.http import HttpResponseRedirect
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from django.views.generic import View
from django.views.generic.base import TemplateResponseMixin
from django.views.generic.detail import SingleObjectMixin
from martor.widgets import MartorWidget
from reversion import revisions
from reversion.models import Revision, Version

from judge.dblock import LockModel
from judge.models import Comment, CommentVote
from judge.utils.raw_sql import unique_together_left_join, RawSQLColumn

ACE_BASE_URL = getattr(settings, 'ACE_BASE_URL', '//cdnjs.cloudflare.com/ajax/libs/ace/1.1.3/')
HIGHLIGHT_BASE_URL = getattr(settings, 'HIGHLIGHT_BASE_URL', '//cdn.bootcss.com/highlight.js/9.12.0/')


class CommentForm(ModelForm):
    class Meta:
        model = Comment
        fields = ['title', 'body', 'parent']
        widgets = {
            'parent': forms.HiddenInput(),
            'body': MartorWidget,
        }

    class Media:
        js = (
            ACE_BASE_URL + 'ace.js',
            ACE_BASE_URL + 'ext-language_tools.js',
            ACE_BASE_URL + 'mode-markdown.js',
            ACE_BASE_URL + 'theme-github.js',
            HIGHLIGHT_BASE_URL + 'highlight.min.js',
        )

    def __init__(self, request, *args, **kwargs):
        self.request = request
        super(CommentForm, self).__init__(*args, **kwargs)
        self.fields['title'].widget.attrs.update({'placeholder': _('Comment title')})
        self.fields['body'].widget.attrs.update({'placeholder': _('Comment body')})

    def clean(self):
        if self.request is not None and self.request.user.is_authenticated:
            profile = self.request.user.profile
            if profile.mute:
                raise ValidationError(_('Your part is silent, little toad.'))
            elif (not self.request.user.is_staff and
                  not profile.submission_set.filter(points=F('problem__points')).exists()):
                raise ValidationError(_('You need to have solved at least one problem '
                                        'before your voice can be heard.'))
        return super(CommentForm, self).clean()


class CommentedDetailView(TemplateResponseMixin, SingleObjectMixin, View):
    comment_page = None

    def get_comment_page(self):
        if self.comment_page is None:
            raise NotImplementedError()
        return self.comment_page

    @method_decorator(login_required)
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        page = self.get_comment_page()

        form = CommentForm(request, request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.author = request.user.profile
            comment.page = page
            with LockModel(write=(Comment, Revision, Version), read=(ContentType,)), revisions.create_revision():
                revisions.set_user(request.user)
                revisions.set_comment(_('Posted comment'))
                comment.save()
            return HttpResponseRedirect(request.path)

        context = self.get_context_data(object=self.object, comment_form=form)
        return self.render_to_response(context)

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        return self.render_to_response(self.get_context_data(
            object=self.object,
            comment_form=CommentForm(request, initial={'page': self.get_comment_page(), 'parent': None})
        ))

    def get_context_data(self, **kwargs):
        context = super(CommentedDetailView, self).get_context_data(**kwargs)
        queryset = Comment.objects.filter(page=self.get_comment_page())
        context['has_comments'] = queryset.exists()
        queryset = queryset.select_related('author__user').defer('author__about').annotate(revisions=Count('versions'))

        if self.request.user.is_authenticated:
            queryset = queryset.annotate(vote_score=Coalesce(RawSQLColumn(CommentVote, 'score'), Value(0)))
            profile = self.request.user.profile
            unique_together_left_join(queryset, CommentVote, 'comment', 'voter', profile.id)
            context['is_new_user'] = (not self.request.user.is_staff and
                                      not profile.submission_set.filter(points=F('problem__points')).exists())
        context['comment_list'] = queryset

        return context
