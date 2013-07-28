#https://docs.djangoproject.com/en/dev/howto/custom-management-commands/#howto-custom-management-commands
from django.core.management.base import BaseCommand, CommandError
from server import data_management as dm
import os


class Command(BaseCommand):
    args = '<block_height>'
    help = 'print the specified chained block on the screen.'

    def handle(self, *args, **options):
        if len(args) != 1:
            raise CommandError('must have one int argument')

        block_height = int(args[0])
        chained_block = dm.load_data(str(block_height), dm.BLOCK_FOLDER)

        self.stdout.write(str(chained_block))