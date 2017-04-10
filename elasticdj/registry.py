from elasticsearch_dsl import DocType
import inspect


class AlreadyRegistered(Exception):
    pass


class DocTypeRegister:
    _registry = []

    def register(self, doctype_class):
        if inspect.isclass(doctype_class) and issubclass(doctype_class, DocType):
            type_ = 'DocType'
        elif callable(doctype_class):
            type_ = 'callable'
        else:
            raise ValueError('Wrapped class must subclass elasticsearch_dsl.DocType or callable.')
        if doctype_class in self._registry:
            raise AlreadyRegistered('The doctype class or callable %s is already registered' % doctype_class.__name__)

        self._registry.append((doctype_class, type_))

    @property
    def doctypes(self):
        return self._registry


doctype_registry = DocTypeRegister()
