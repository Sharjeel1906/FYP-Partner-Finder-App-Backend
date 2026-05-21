from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("FYP_Partner_Finder", "0008_alter_team_group_lead"),
    ]

    operations = [
        migrations.AddField(
            model_name="userprofile",
            name="is_online",
            field=models.BooleanField(default=False),
        ),
    ]
