# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2016-03-01 07:37
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sanat', '0004_auto_20160229_0810'),
    ]

    operations = [
        migrations.AddField(
            model_name='wordstatus',
            name='last_streak',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]