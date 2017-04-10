from django.core.management.base import BaseCommand
# from django.conf import settings
from elasticsearch_dsl import Index
from elasticsearch.exceptions import NotFoundError
import elasticdj
# from django.utils import translation
from django.core.management import call_command
from elasticdj.models import Log
from django.utils import timezone


elasticdj.autodiscover()


class Command(BaseCommand):
    help = 'Rebuilds Elasticsearch index'

    def handle(self, **options):
        log = Log.objects.create(command="rebuild")
        # translation.activate(settings.LANGUAGE_CODE)
        verbosity = int(options['verbosity'])
        doctypes = elasticdj.doctype_registry.doctypes
        indexes = {}
        for doctype, t in doctypes:
            if t == 'DocType':
                indexes[doctype._doc_type.index] = indexes.get(doctype._doc_type.index, Index(doctype._doc_type.index))
        for index_name, index in indexes.items():
            try:
                if verbosity > 1:
                    print 'Deleting index:', index_name
                index.delete()
            except NotFoundError:
                if verbosity > 1:
                    print 'IndexNotFound'
                pass
        options['is_update'] = False
        call_command('update_index', **options)
        log.finished_at = timezone.now()
        log.save()
