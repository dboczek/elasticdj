from django.core.management.base import BaseCommand
from django.conf import settings
from elasticsearch_dsl import Index
from django.utils import translation
from django.utils import timezone
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
import time
from datetime import timedelta
import elasticdj
import certifi
from elasticdj.models import Log


elasticdj.autodiscover()


class scroll_hits_iterator:
    def __init__(self, elasticsearch=None, scroll='10m', **kwargs):
        self.es = elasticsearch or Elasticsearch(
            settings.ELASTICSEARCH_HOSTS, verify_certs=True, ca_certs=certifi.where())
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


def update(is_update=True, is_run_from_commandline=False, **options):
    output = []

    def summary(message):
        if is_run_from_commandline:
            print message
        else:
            output.append(message)

    if is_update:
        log = Log.objects.create(command="update")
    total_timer = Timer('Total time').start()
    verbosity = int(options['verbosity'])
    translation.activate(settings.LANGUAGE_CODE)

    indexes = {}

    doctypes = elasticdj.doctype_registry.doctypes

    if options["doctype"]:
        mapping = dict((d.__name__, d) for d, t in doctypes)
        doctypes = [(mapping[doctype], 'DocType') for doctype in options['doctype']]

    if verbosity:
        # import ipdb;ipdb.set_trace()
        summary("Preparing to index: %s" % ', '.join([cls.__name__ for cls, t in doctypes if t == 'DocType']))

    for doctype, t in doctypes:
        if t == 'DocType':
            indexes[doctype._doc_type.index] = indexes.get(doctype._doc_type.index, Index(doctype._doc_type.index))
            indexes[doctype._doc_type.index].doc_type(doctype)
    for index in indexes.values():
        if not index.exists():
            index.create()
    index_start_at = timezone.now()
    if verbosity:
        summary('Start index at %s' % index_start_at)
    timers = []
    for doctype, t in doctypes:
        if t == 'DocType':
            timer = Timer('%s indexing time' % doctype.__name__).start()
            if verbosity:
                summary("Indexing: %s" % doctype.__name__)
            for obj in doctype.get_queryset(for_update=is_update):
                d = doctype(obj)
                if verbosity > 1:
                    summary("%s %s [%s] %s" % (d.indexed_at, doctype.__name__, obj.pk, obj))
                d.upsert()
            if verbosity:
                summary("%s %s" % (timer.name, timer.stop().time()))
            timers.append(timer)
        else:  # callable
            messages = doctype()
            if is_run_from_commandline:
                if verbosity:
                    for m in messages:
                        print "\t", m
            else:
                output += messages
    if not options["doctype"]:
        if verbosity:
            summary("Removing outdated documents.")

        time.sleep(2)  # wait for Elastic Search to reindex documents.

        timer = Timer('Removing outdated document time').start()
        es = Elasticsearch(settings.ELASTICSEARCH_HOSTS, verify_certs=True, ca_certs=certifi.where())

        body = {
            "query": {
                "bool": {
                    "filter": {"range": {"indexed_at": {"lt": index_start_at}}}
                }
            }
        }
        for index in indexes.keys():
            docs = scroll_hits_iterator(es, index=index, body=body,
                                        fields=['indexed_at'], sort="_doc")
            result = bulk(es, delete_actions(docs, verbosity))
            if verbosity:
                summary('Removed %d documents.' % result[0])
                if result[1]:
                    # TODO log error when logger will be configured.
                    summary("Errors:")
                    for error in result[1]:
                        summary(error)

    if verbosity:
        summary("%s %s" % (timer.name, timer.stop().time()))

    timers.append(timer)

    if verbosity:
        summary('Indexing total time: %s' % total_timer.stop().time())
    if verbosity > 1:
        for timer in timers:
            summary("%s %s" % (timer.name, timer.time()))

    if is_update:
        log.finished_at = timezone.now()
        log.save()
    return output


class Command(BaseCommand):
    help = 'Updates Elasticsearch index'

    def add_arguments(self, parser):
        parser.add_argument('doctype', nargs='*', type=str)

    def handle(self, is_update=True, **options):
        return update(is_update, is_run_from_commandline=True, **options)
