import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("accounts", "0001_initial")]

    operations = [
        migrations.CreateModel(
            name="ProfilePicture",
            fields=[
                ("user", models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    primary_key=True,
                    serialize=False,
                    to=settings.AUTH_USER_MODEL,
                )),
                ("image", models.BinaryField(editable=False)),
            ],
        ),
        migrations.RunSQL(
            "ALTER TABLE accounts_profilepicture ENABLE ROW LEVEL SECURITY",
            "ALTER TABLE accounts_profilepicture DISABLE ROW LEVEL SECURITY",
        ),
    ]
