# Generated by Django 2.2.8 on 2020-04-03 07:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0006_auto_20200403_0731'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cpcs_user',
            name='matchDist',
            field=models.CharField(choices=[('1', '1 arcsec'), ('2', '2 arcsec'), ('4', '4 arcsec'), ('6', '6 arcsec')], default='1 arcsec', max_length=10, verbose_name='Matching radius'),
        ),
    ]
