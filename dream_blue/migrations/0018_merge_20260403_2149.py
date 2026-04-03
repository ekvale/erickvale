# Merges parallel heads:
#   0016_alter_businesscalendarevent_square_footage
#   0017_rollover_vacancy_pipeline
#
# After merge, run: python manage.py migrate dream_blue
# (Otherwise models expect columns from 0016_books while DB may only have the alter branch.)

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dream_blue', '0016_alter_businesscalendarevent_square_footage'),
        ('dream_blue', '0017_rollover_vacancy_pipeline'),
    ]

    operations = []
