# Generated by Django 4.0.3 on 2022-03-24 10:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('flickr', '0028_alter_user_iconfarm'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='user',
            options={'ordering': ['realname', 'username']},
        ),
        migrations.AlterField(
            model_name='user',
            name='realname',
            field=models.CharField(blank=True, max_length=255),
        ),
    ]