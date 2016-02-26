from .registry import doctype_registry


def register(doctype_class):
    doctype_registry.register(doctype_class)
    return doctype_class
