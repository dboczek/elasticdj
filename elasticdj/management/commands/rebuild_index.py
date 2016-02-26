from django.core.management.base import BaseCommand
from django.conf import settings
from elasticsearch_dsl import Index
from elasticsearch.exceptions import NotFoundError
# from django.utils import translation
from django.core.management import call_command


class Command(BaseCommand):
    help = 'Rebuilds Elasticsearch index'

    def handle(self, **options):
        # translation.activate(settings.LANGUAGE_CODE)
        main = Index(settings.ELASTICSEARCH_INDEX_NAME)
        try:
            main.delete()
        except NotFoundError:
            pass
        call_command('update_index', **options)
