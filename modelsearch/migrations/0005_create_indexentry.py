# Generated by Django 3.2.4 on 2021-06-28 14:12

import django.db.models.deletion

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("contenttypes", "0002_remove_content_type_name"),
        ("wagtailsearch", "0004_querydailyhits_verbose_name_plural"),
    ]

    operations = [
        migrations.CreateModel(
            name="IndexEntry",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("object_id", models.CharField(max_length=50)),
                ("title_norm", models.FloatField(default=1.0)),
                (
                    "content_type",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="+",
                        to="contenttypes.contenttype",
                    ),
                ),
            ],
            options={
                "verbose_name": "index entry",
                "verbose_name_plural": "index entries",
                "abstract": False,
            },
        ),
        migrations.AlterUniqueTogether(
            name="indexentry",
            unique_together={("content_type", "object_id")},
        ),
    ]
