# Generated by Django 4.2 on 2024-07-27 06:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auctions', '0019_remove_auctionlist_top_bid'),
    ]

    operations = [
        migrations.AlterField(
            model_name='auctionlist',
            name='image_url',
            field=models.ImageField(blank=True, null=True, upload_to='auction_image'),
        ),
    ]
