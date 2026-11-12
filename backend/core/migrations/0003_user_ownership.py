from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

def assign_legacy(apps, schema_editor):
    User=apps.get_model(*settings.AUTH_USER_MODEL.split("."))
    user,_=User.objects.using(schema_editor.connection.alias).get_or_create(username="legacy-unassigned",defaults={"is_active":False})
    for name in ["Project","DevEvent","FocusSession","DomainAsset","HostingService","AISubscription"]:
        apps.get_model("core",name).objects.using(schema_editor.connection.alias).filter(owner__isnull=True).update(owner_id=user.pk)

class Migration(migrations.Migration):
    dependencies=[("core","0002_infrastructure_subscriptions"),migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations=[
        migrations.CreateModel(name="ClerkProfile",fields=[("id",models.BigAutoField(primary_key=True,serialize=False,auto_created=True,verbose_name="ID")),("clerk_user_id",models.CharField(max_length=255,unique=True,db_index=True)),("created_at",models.DateTimeField(auto_now_add=True)),("user",models.OneToOneField(to=settings.AUTH_USER_MODEL,on_delete=django.db.models.deletion.CASCADE,related_name="clerk_profile"))]),
        *[migrations.AddField(model_name=n.lower(),name="owner",field=models.ForeignKey(to=settings.AUTH_USER_MODEL,on_delete=django.db.models.deletion.CASCADE,null=True,related_name=n.lower()+"_owned")) for n in ["Project","DevEvent","FocusSession","DomainAsset","HostingService","AISubscription"]],
        migrations.RunPython(assign_legacy,migrations.RunPython.noop),
        *[migrations.AlterField(model_name=n.lower(),name="owner",field=models.ForeignKey(to=settings.AUTH_USER_MODEL,on_delete=django.db.models.deletion.CASCADE,related_name=rel)) for n,rel in [("Project","projects"),("DevEvent","dev_events"),("FocusSession","focus_sessions"),("DomainAsset","domain_assets"),("HostingService","hosting_services"),("AISubscription","ai_subscriptions")]],
        migrations.AlterField(model_name="project",name="path",field=models.TextField()),
        migrations.AlterField(model_name="domainasset",name="domain_name",field=models.CharField(max_length=253)),
        migrations.AddConstraint(model_name="project",constraint=models.UniqueConstraint(fields=("owner","path"),name="uniq_project_owner_path")),
        migrations.AddConstraint(model_name="domainasset",constraint=models.UniqueConstraint(fields=("owner","domain_name"),name="uniq_domain_owner_name")),
    ]
