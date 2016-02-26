from elasticsearch_dsl import Search


class ElasticQuerySet(object):
    def __init__(self, doctype=None):
        self.doctype
        self.search = self._all()

    def _all(self):
        search = Search()
        if self.doctype:
            search = self.search.doc_type(self.doctype)
        return search

    def all(self):
        self.search = self._all()
        return self

    def filter(self, *args, **kwargs):
        pass
