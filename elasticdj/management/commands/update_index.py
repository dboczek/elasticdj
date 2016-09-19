from django.core.management.base import BaseCommand
from django.conf import settings
from elasticsearch_dsl import Index
from elasticsearch_dsl import exceptions
from django.utils import translation
from django.utils import timezone
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
import time
from datetime import timedelta
import elasticdj

elasticdj.autodiscover()


class scroll_hits_iterator:
    def __init__(self, elasticsearch=None, scroll='10m', **kwargs):
        self.es = elasticsearch or Elasticsearch(settings.ELASTICSEARCH_HOSTS)
        self.scroll = scroll
        self.kwargs = kwargs
        self.i = 0
        self.hits = None
        self.scroll_id = None

    def __iter__(self):
        return self

    def _get_hits(self):
        if not self.scroll_id:
            result = self.es.search(scroll=self.scroll, **self.kwargs)
            self.scroll_id = result['_scroll_id']
        else:
            result = self.es.scroll(scroll_id=self.scroll_id, scroll=self.scroll)
        return result['hits']['hits']

    def next(self):
            if not self.hits or self.i >= len(self.hits):
                self.hits = self._get_hits()
                self.i = 0
                if not self.hits:
                    raise StopIteration()

            hit = self.hits[self.i]
            self.i += 1
            return hit


def delete_actions(documents, verbosity=1):
    for document in documents:
        if verbosity > 1:
            print 'Removing:', document
        document['_op_type'] = 'delete'
        yield document


class TimerException(Exception):
    pass


class Timer:

    def __init__(self, name="Default"):
        self.start_time = None
        self.stop_time = None
        self.name = name

    def start(self):
        self.start_time = time.time()
        return self

    def stop(self):
        self.stop_time = time.time()
        return self

    def reset(self):
        self.start_time = self.stop_time = None
        return self

    def time(self):
        assert self.start_time is not None, "Timer should be started."
        end = self.stop_time or time.time()
        elapsed_seconds = (end - self.start_time)
        return timedelta(seconds=elapsed_seconds)


class Command(BaseCommand):
    help = 'Updates Elasticsearch index'

    def handle(self, **options):
        total_timer = Timer('Total time').start()
        verbosity = int(options['verbosity'])
        translation.activate(settings.LANGUAGE_CODE)

        main = Index(settings.ELASTICSEARCH_INDEX_NAME)

        doctypes = elasticdj.doctype_registry.doctypes

        if verbosity:
            print "Preparing to index: %s" % ', '.join([cls.__name__ for cls in doctypes])

        if not main.exists():
            main.create()
        for doctype in doctypes:
            try:
                doctype.init()
            except exceptions.IllegalOperation:
                pass
        index_start_at = timezone.now()
        if verbosity:
            print 'Start index at', index_start_at
        timers = []
        for doctype in doctypes:
            timer = Timer('%s indexing time' % doctype.__name__).start()
            if verbosity:
                print "Indexing: %s" % doctype.__name__

            for obj in doctype.index_queryset():
                d = doctype(obj)
                if verbosity > 1:
                    print d.indexed_at, doctype.__name__, "[%s]" % obj.pk, obj
                d.save()
            if verbosity:
                print timer.name, timer.stop().time()
            timers.append(timer)

        if verbosity:
            print "Removing outdated documents."

        time.sleep(2)  # wait for Elastic Search to reindex documents.

        timer = Timer('Removing outdated document time').start()
        from elasticsearch import Elasticsearch
        es = Elasticsearch(settings.ELASTICSEARCH_HOSTS)

        body = {
            "query": {
                "bool": {
                    "filter": {"range": {"indexed_at": {"lt": index_start_at}}}
                }
            }
        }
        docs = scroll_hits_iterator(es, index=settings.ELASTICSEARCH_INDEX_NAME, body=body,
                                    fields=['indexed_at'], sort="_doc")
        # for doc in delete_actions(docs, verbosity):
        #    pass
        result = bulk(es, delete_actions(docs, verbosity))
        if verbosity:
            print 'Removed %d documents.' % result[0]
            if result[1]:
                # TODO log error when logger will be configured.
                print "Errors:"
                for error in result[1]:
                    print error

        if verbosity:
            print timer.name, timer.stop().time()

        timers.append(timer)

        if verbosity:
            print 'Indexing total time: %s' % total_timer.stop().time()
        if verbosity > 1:
            for timer in timers:
                print timer.name, timer.time()
