# Generated by Django 5.0.1 on 2024-01-15 12:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auctions', '0010_alter_auctionlist_expire_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='auctionlist',
            name='expire_date',
            field=models.DateTimeField(null=True),
        ),
    ]
