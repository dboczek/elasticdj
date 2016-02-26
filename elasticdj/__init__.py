from django.utils.module_loading import autodiscover_modules
from .registry import doctype_registry

__version__ = '1.0rc1'

__all__ = [
    "doctype_registry", "autodiscover",
]


def autodiscover():
    autodiscover_modules('elastic_documents', register_to=doctype_registry)
