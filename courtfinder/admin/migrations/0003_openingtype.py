# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2018-04-10 10:28
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('admin', '0002_contacttype'),
    ]

    operations = [
        migrations.CreateModel(
            name='OpeningType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
            ],
        ),
    ]
