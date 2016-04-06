# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2016-02-28 12:22
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Answer',
            fields=[
                ('aid', models.IntegerField(primary_key=True, serialize=False)),
                ('sid', models.IntegerField()),
                ('lid', models.IntegerField()),
                ('wlid', models.IntegerField()),
                ('ts', models.DateTimeField(auto_now_add=True)),
                ('q', models.CharField(max_length=256)),
                ('a', models.CharField(max_length=256)),
                ('c', models.CharField(max_length=256)),
                ('correct', models.FloatField()),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Hint',
            fields=[
                ('hid', models.IntegerField(primary_key=True, serialize=False)),
                ('ts', models.DateTimeField(auto_now_add=True)),
                ('lid', models.IntegerField()),
                ('wlid', models.IntegerField()),
                ('q', models.CharField(max_length=256)),
                ('hint', models.CharField(max_length=256)),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='WordStatus',
            fields=[
                ('wid', models.IntegerField(primary_key=True, serialize=False)),
                ('lid', models.IntegerField()),
                ('wlid', models.IntegerField()),
                ('last_ts', models.DateTimeField()),
                ('last_c_ts', models.DateTimeField()),
                ('last_seq', models.IntegerField()),
                ('last_c_seq', models.IntegerField()),
                ('c_short', models.FloatField()),
                ('c_med', models.FloatField()),
                ('c_long', models.FloatField()),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AlterIndexTogether(
            name='wordstatus',
            index_together=set([('lid', 'wlid')]),
        ),
    ]