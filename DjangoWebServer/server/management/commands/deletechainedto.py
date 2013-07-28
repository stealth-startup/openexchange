#https://docs.djangoproject.com/en/dev/howto/custom-management-commands/#howto-custom-management-commands
from django.core.management.base import BaseCommand, CommandError
from server import data_management as dm
import os


class Command(BaseCommand):
    args = '<block_height>'
    help = 'delete chained state to a specified height (inclusive)'

    def handle(self, *args, **options):
        if len(args) != 1:
            raise CommandError('must have one argument')

        from_height = int(args[0])

        indexes = [int(f) for f in os.listdir(dm.BLOCK_FOLDER)
                   if os.path.isfile(os.path.join(dm.BLOCK_FOLDER, f)) and f.isdigit()]
        for index in indexes:
            if index <= from_height:
                self.stdout.write('removing %d' % index)
                dm.remove_data(str(index), dm.BLOCK_FOLDER, silent=True)
                self.stdout.write('%d removed' % index)

        self.stdout.write('done')