from django.apps import AppConfig
from django.db import DatabaseError
from django.utils.translation import ugettext_lazy
from suit import apps
from suit.apps import DjangoSuitConfig
from suit.menu import ParentItem, ChildItem


class JudgeAppConfig(AppConfig):
    name = 'judge'
    verbose_name = ugettext_lazy('HBU Online Judge')

    def ready(self):
        # WARNING: AS THIS IS NOT A FUNCTIONAL PROGRAMMING LANGUAGE,
        #          OPERATIONS MAY HAVE SIDE EFFECTS.
        #          DO NOT REMOVE THINKING THE IMPORT IS UNUSED.
        # noinspection PyUnresolvedReferences
        from . import signals, jinja2

        from django.contrib.flatpages.models import FlatPage
        from django.contrib.flatpages.admin import FlatPageAdmin
        from django.contrib import admin
        from django.contrib.auth.models import User
        from admin.user import MyUserAdmin
        from reversion.admin import VersionAdmin

        class FlatPageVersionAdmin(VersionAdmin, FlatPageAdmin):
            suit_form_size = {
                'fields': {
                    'content': apps.SUIT_FORM_SIZE_FULL
                },
            }

        admin.site.unregister(FlatPage)
        admin.site.register(FlatPage, FlatPageVersionAdmin)
        admin.site.unregister(User)
        admin.site.register(User, MyUserAdmin)
        from judge.models import Language, Profile

        try:
            lang = Language.get_python2()
            for user in User.objects.filter(profile=None):
                # These poor profileless users
                profile = Profile(user=user, language=lang)
                profile.save()
        except DatabaseError:
            pass


class SuitConfig(DjangoSuitConfig):
    verbose_name = 'HBU Online Judge Suit'
    menu = (
        ParentItem('Problem', children=[
            ChildItem(model='judge.problem'),
            ChildItem(model='judge.problemgroup'),
            ChildItem(model='judge.Problemtype'),
        ], icon='fa fa-question-circle'),
        ParentItem('Submission', children=[
            ChildItem(model='judge.submission'),
            ChildItem(model='judge.language'),
            ChildItem(model='judge.judge'),
        ], icon='fa fa-check-square-o'),
        ParentItem('Contest', children=[
            ChildItem(model='judge.contest'),
            ChildItem(model='judge.contestparticipation'),
            ChildItem(model='judge.contesttag'),
        ], icon='fa fa-bar-chart'),
        ParentItem('User', children=[
            ChildItem(model='auth.user'),
            ChildItem(model='judge.profile'),
            ChildItem(model='judge.organization'),
            ChildItem(model='judge.organizationrequest'),
        ], icon='fa fa-user'),
        ParentItem('Site', children=[
            ChildItem(model='judge.blogpost'),
            ChildItem(model='judge.navigationbar'),
            ChildItem(model='judge.miscConfig'),
            ChildItem(model='judge.license'),
            ChildItem(model='sites.site'),
            ChildItem(model='redirects.redirect'),
            ChildItem(model='judge.comment'),
            ChildItem(model='flatpages.flatpage'),
            ChildItem(model='judge.solution'),
        ], icon='fa fa-leaf'),
    )
