#https://docs.djangoproject.com/en/dev/howto/custom-management-commands/#howto-custom-management-commands
from django.core.management.base import NoArgsCommand
import openexchangelib
from openexchangelib import types as oel_types
from server.models import ChainedState, StaticData
import server.data_management as dm


class Command(NoArgsCommand):
    help = 'Initialize ChainedState. Run this command before start the web server.'

    def handle_noargs(self, **options):
        self.stdout.write('initializing chained state')
        chained_state = ChainedState(openexchangelib.exchange0())
        ChainedState._global_instance = chained_state

        dm.push_chained_state(chained_state)
        self.stdout.write('chained_state saved')

