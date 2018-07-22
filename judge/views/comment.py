from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db import IntegrityError, transaction
from django.db.models import F
from django.forms.models import ModelForm
from django.http import HttpResponseForbidden, HttpResponseBadRequest, HttpResponse, Http404
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext as _
from django.views.decorators.http import require_POST
from django.views.generic import DetailView, UpdateView
from martor.widgets import MartorWidget
from reversion import revisions
from reversion.models import Version

from judge.dblock import LockModel
from judge.models import Comment, CommentVote
from judge.utils.views import TitleMixin

ACE_BASE_URL = getattr(settings, 'ACE_BASE_URL', '//cdnjs.cloudflare.com/ajax/libs/ace/1.1.3/')
HIGHLIGHT_BASE_URL = getattr(settings, 'HIGHLIGHT_BASE_URL', '//cdn.bootcss.com/highlight.js/9.12.0/')

__all__ = ['upvote_comment', 'downvote_comment', 'CommentEditAjax', 'CommentContent',
           'CommentEdit']


@login_required
def vote_comment(request, delta):
    if abs(delta) != 1:
        return HttpResponseBadRequest(_('Messing around, are we?'), content_type='text/plain')

    if request.method != 'POST':
        return HttpResponseForbidden()

    if 'id' not in request.POST:
        return HttpResponseBadRequest()

    try:
        comment_id = int(request.POST['id'])
    except ValueError:
        return HttpResponseBadRequest()
    else:
        if not Comment.objects.filter(id=comment_id).exists():
            raise Http404()

    vote = CommentVote()
    vote.comment_id = comment_id
    vote.voter = request.user.profile
    vote.score = delta

    while True:
        try:
            vote.save()
        except IntegrityError:
            with LockModel(write=(CommentVote,)):
                try:
                    vote = CommentVote.objects.get(comment_id=comment_id, voter=request.user.profile)
                except CommentVote.DoesNotExist:
                    # We must continue racing in case this is exploited to manipulate votes.
                    continue
                if -vote.score != delta:
                    return HttpResponseBadRequest(_('You already voted.'), content_type='text/plain')
                vote.delete()
            Comment.objects.filter(id=comment_id).update(score=F('score') - vote.score)
        else:
            Comment.objects.filter(id=comment_id).update(score=F('score') + delta)
        break
    return HttpResponse('success', content_type='text/plain')


def upvote_comment(request):
    return vote_comment(request, 1)


def downvote_comment(request):
    return vote_comment(request, -1)


class CommentMixin(object):
    model = Comment
    pk_url_kwarg = 'id'
    context_object_name = 'comment'


class CommentRevisionAjax(CommentMixin, DetailView):
    template_name = 'comments/revision-ajax.html'

    def get_context_data(self, **kwargs):
        context = super(CommentRevisionAjax, self).get_context_data(**kwargs)
        revisions = Version.objects.get_for_object(self.object).order_by('-revision')
        try:
            wanted = min(max(int(self.request.GET.get('revision', 0)), 0), len(revisions) - 1)
        except ValueError:
            raise Http404
        context['revision'] = revisions[wanted]
        return context

    def get_object(self, queryset=None):
        comment = super(CommentRevisionAjax, self).get_object(queryset)
        if comment.hidden and not self.request.user.has_perm('judge.change_comment'):
            raise Http404()
        return comment


class CommentEditForm(ModelForm):
    class Meta:
        model = Comment
        fields = ['title', 'body']
        widgets = {'body': MartorWidget(attrs={'id': 'id-edit-comment-body'})}

    class Media:
        js = (
            ACE_BASE_URL + 'ace.js',
            ACE_BASE_URL + 'ext-language_tools.js',
            ACE_BASE_URL + 'mode-markdown.js',
            ACE_BASE_URL + 'theme-github.js',
            HIGHLIGHT_BASE_URL + 'highlight.min.js',
        )


class CommentEditAjax(LoginRequiredMixin, CommentMixin, UpdateView):
    template_name = 'comments/edit-ajax.html'
    form_class = CommentEditForm

    def form_valid(self, form):
        with transaction.atomic(), revisions.create_revision():
            revisions.set_comment(_('Edited from site'))
            revisions.set_user(self.request.user)
            return super(CommentEditAjax, self).form_valid(form)

    def get_success_url(self):
        return self.object.get_absolute_url()

    def get_object(self, queryset=None):
        comment = super(CommentEditAjax, self).get_object(queryset)
        if self.request.user.has_perm('judge.change_comment'):
            return comment
        profile = self.request.user.profile
        if profile != comment.author or profile.mute or comment.hidden:
            raise Http404()
        return comment


class CommentEdit(TitleMixin, CommentEditAjax):
    template_name = 'comments/edit.html'

    def get_title(self):
        return _('Editing comment')


class CommentContent(CommentMixin, DetailView):
    template_name = 'comments/content.html'


class CommentVotesAjax(PermissionRequiredMixin, CommentMixin, DetailView):
    template_name = 'comments/votes.html'
    permission_required = 'judge.change_commentvote'

    def get_context_data(self, **kwargs):
        context = super(CommentVotesAjax, self).get_context_data(**kwargs)
        context['votes'] = (self.object.votes.select_related('voter__user')
                            .only('id', 'voter__display_rank', 'voter__user__username', 'score'))
        return context


@require_POST
def comment_hide(request):
    if not request.user.has_perm('judge.change_comment'):
        raise PermissionDenied()
    try:
        comment_id = int(request.POST['id'])
    except ValueError:
        return HttpResponseBadRequest()

    comment = get_object_or_404(Comment, id=comment_id)
    comment.hidden = True
    comment.save(update_fields=['hidden'])
    return HttpResponse('ok')
