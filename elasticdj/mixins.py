from django.utils import timezone


class ModelMixin(object):

    def __init__(self, instance=None, meta=None, **kwargs):
        super(ModelMixin, self).__init__(meta=meta, **kwargs)
        if instance:
            self.meta.id = instance.id
            self.prepare(instance)

    def prepare(self, instance):
        for field_name in self._doc_type.mapping.properties._params['properties'].keys():
            if getattr(self, field_name, None) in [None, '']:
                value = getattr(instance, field_name, None)
                if value is not None:
                    setattr(self, field_name, value)
        setattr(self, 'indexed_at', timezone.now())

    @classmethod
    def index_queryset(cls):
        """Used when the entire index for model is updated."""
        return cls.get_model().objects.all()

    @classmethod
    def get_model(cls):
        raise NotImplementedError
