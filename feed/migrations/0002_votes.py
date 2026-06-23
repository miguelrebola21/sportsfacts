from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("feed", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="fact",
            name="downvotes",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="fact",
            name="upvotes",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="record",
            name="downvotes",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="record",
            name="upvotes",
            field=models.PositiveIntegerField(default=0),
        ),
    ]
