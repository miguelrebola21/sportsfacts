from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Tag",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=80, unique=True)),
            ],
            options={"ordering": ("name",)},
        ),
        migrations.CreateModel(
            name="Fact",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("text", models.TextField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("tags", models.ManyToManyField(blank=True, related_name="facts", to="feed.tag")),
            ],
            options={"ordering": ("id",)},
        ),
        migrations.CreateModel(
            name="Record",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("number", models.PositiveIntegerField(unique=True)),
                ("text", models.TextField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("tags", models.ManyToManyField(blank=True, related_name="records", to="feed.tag")),
            ],
            options={"ordering": ("number",)},
        ),
    ]
