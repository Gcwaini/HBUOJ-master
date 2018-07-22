from django.conf import settings
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from import_export import resources, fields, widgets
from import_export.admin import ImportExportModelAdmin

from judge.models import Profile, Language, Organization

DEFAULT_USER_LANGUAGE = getattr(settings,
                                'DEFAULT_USER_LANGUAGE',
                                'CPP11')


class UserResource(resources.ModelResource):
    name = fields.Field(attribute='profile__name')
    about = fields.Field(attribute='profile__about')
    organizations = fields.Field(widget=widgets.ManyToManyWidget(model=Organization, field='key'),
                                 attribute='profile__organizations')

    _profile = Profile()

    def init_instance(self, row=None):
        usr = super(UserResource, self).init_instance(row)
        usr.is_active = True
        self._profile.language = Language.objects.get(key=DEFAULT_USER_LANGUAGE)
        usr.profile = self._profile
        return usr

    def before_save_instance(self, instance, using_transactions, dry_run):
        if not using_transactions and dry_run:
            # we don't have transactions and we want to do a dry_run
            pass
        else:
            instance.set_password(instance.password)

    def after_save_instance(self, instance, using_transactions, dry_run):
        if not using_transactions and dry_run:
            # we don't have transactions and we want to do a dry_run
            pass
        else:
            Profile.objects.update_or_create(user=instance, defaults=self._profile)

    class Meta:
        model = User
        fields = ('username', 'password', 'email',)
        export_order = ('username', 'email', 'name', 'about', 'organizations')
        import_id_fields = ('username',)


class MyUserAdmin(UserAdmin, ImportExportModelAdmin):
    resource_class = UserResource
