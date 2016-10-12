from django.core.management.base import BaseCommand
# from django.conf import settings
from elasticsearch_dsl import Index
from elasticsearch.exceptions import NotFoundError
import elasticdj
# from django.utils import translation
from django.core.management import call_command

elasticdj.autodiscover()


class Command(BaseCommand):
    help = 'Rebuilds Elasticsearch index'

    def handle(self, **options):
        # translation.activate(settings.LANGUAGE_CODE)
        doctypes = elasticdj.doctype_registry.doctypes
        indexes = {}
        for doctype in doctypes:
            indexes[doctype._doc_type.index] = indexes.get(doctype._doc_type.index, Index(doctype._doc_type.index))
        for index in indexes.values():
            try:
                index.delete()
            except NotFoundError:
                pass
        call_command('update_index', **options)
