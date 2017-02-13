from django.utils import timezone
from elasticsearch_dsl.document import DOC_META_FIELDS, META_FIELDS


class ModelMixin(object):

    def __init__(self, instance=None, for_update=False, meta=None, **kwargs):
        super(ModelMixin, self).__init__(meta=meta, **kwargs)
        if instance:
            self.meta.id = instance.id
            self.prepare(instance, for_update=for_update)

    def prepare(self, instance, for_update):
        for field_name in self._doc_type.mapping.properties._params['properties'].keys():
            if getattr(self, field_name, None) in [None, '']:
                try:
                    value = getattr(instance, field_name)
                except AttributeError:
                    pass
                else:
                    setattr(self, field_name, value)
        setattr(self, 'indexed_at', timezone.now())

    def upsert(self, using=None, index=None):
        es = self._get_connection(using)

        # extract parent, routing etc from meta
        doc_meta = dict(
            (k, self.meta[k])
            for k in DOC_META_FIELDS
            if k in self.meta
        )
        meta = es.update(
            index=self._get_index(index),
            doc_type=self._doc_type.name,
            body={
                'doc': self.to_dict(),
                'doc_as_upsert': True,
            },
            **doc_meta
        )
        # update meta information from ES
        for k in META_FIELDS:
            if '_' + k in meta:
                setattr(self.meta, k, meta['_' + k])

    @classmethod
    def index_queryset(cls):
        """Used when the entire index for model is rebuild."""
        return cls.get_model().objects.all()

    @classmethod
    def get_queryset(cls, for_update=False):
        if for_update and callable(getattr(cls, 'update_queryset', None)):
            return cls.update_queryset()
        return cls.index_queryset()

    @classmethod
    def get_model(cls):
        raise NotImplementedError
