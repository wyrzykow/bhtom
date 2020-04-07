# Generated by Django 2.2.8 on 2020-04-06 15:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0007_auto_20200403_0731'),
    ]

    operations = [
        migrations.RenameField(
            model_name='bhtomfits',
            old_name='user_id',
            new_name='user',
        ),
        migrations.AddField(
            model_name='bhtomfits',
            name='cpcs_result',
            field=models.FileField(blank=True, editable=False, null=True, upload_to='calibrations'),
        ),
        migrations.AlterField(
            model_name='cpcs_user',
            name='matchDist',
            field=models.CharField(choices=[('1', '1 arcsec'), ('6', '6 arcsec'), ('2', '2 arcsec'), ('4', '4 arcsec')], default='1 arcsec', max_length=10, verbose_name='Matching radius'),
        ),
    ]
