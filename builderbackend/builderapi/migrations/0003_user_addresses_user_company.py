# Generated by Django 5.2.4 on 2025-07-30 04:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('builderapi', '0002_blogpost_layout'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='addresses',
            field=models.JSONField(default=list),
        ),
        migrations.AddField(
            model_name='user',
            name='company',
            field=models.CharField(blank=True, max_length=200),
        ),
    ]
