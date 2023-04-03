# Generated by Django 3.2.15 on 2023-04-03 19:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('foodcartapp', '0038_auto_20230403_2153'),
    ]

    operations = [
        migrations.RemoveIndex(
            model_name='order',
            name='foodcartapp_firstna_b9b5f7_idx',
        ),
        migrations.RenameField(
            model_name='order',
            old_name='address',
            new_name='customer_address',
        ),
        migrations.RenameField(
            model_name='order',
            old_name='firstname',
            new_name='customer_firstname',
        ),
        migrations.RenameField(
            model_name='order',
            old_name='lastname',
            new_name='customer_lastname',
        ),
        migrations.RenameField(
            model_name='order',
            old_name='phonenumber',
            new_name='customer_phone',
        ),
        migrations.AddIndex(
            model_name='order',
            index=models.Index(fields=['customer_firstname', 'customer_lastname'], name='foodcartapp_custome_f73a9a_idx'),
        ),
    ]
