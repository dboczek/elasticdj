from elasticsearch_dsl import DocType


class AlreadyRegistered(Exception):
    pass


class DocTypeRegister:
    _registry = []

    def register(self, doctype_class):
        if not issubclass(doctype_class, DocType):
            raise ValueError('Wrapped class must subclass elasticsearch_dsl.DocType.')
        if doctype_class in self._registry:
            raise AlreadyRegistered('The doctype class %s is already registered' % doctype_class.__name__)

        self._registry.append(doctype_class)

    @property
    def doctypes(self):
        return self._registry


doctype_registry = DocTypeRegister()
