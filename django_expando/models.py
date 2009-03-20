from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.utils.encoding import smart_unicode

class ExpandoManager(models.Manager):
    def get_for_model(self, model):
        ct = ContentType.objects.get_for_model(model)
        return self.model.objects.filter(content_type=ct)

    def get_for_object(self, object):
        pk = smart_unicode(object.pk)
        return self.get_for_model(object).filter(object_pk=pk)

    def delete_for_object(self, object):
        self.get_for_object(object).delete()

    def get_for_key(self, object, key):
        return self.get_for_object(object).get(key=key)

    def set_for_key(self, object, key):
        value = smart_unicode(object.__dict__[key])
        e = self.model(
            content_type = ContentType.objects.get_for_model(object),
            object_pk = smart_unicode(object.pk),
            key = key,
            value = value
        )
        e.save(force_insert=True)

    def filter_for_model_qs(self, model_qs, **kwargs):
        qs = self.get_for_model(model_qs.model)
        for k,v in kwargs.items():
            qs = qs.filter(key=k, value__iexact=v)
        pks = qs.values_list('object_pk', flat=True)
        return model_qs.filter(pk__in=pks)

class Expando(models.Model):
    content_type = models.ForeignKey(ContentType)
    object_pk    = models.TextField('object id', db_index=True)
    key          = models.CharField('expando key', max_length=32, db_index=True)
    value        = models.TextField('expando value')
    
    objects = ExpandoManager()

    class Meta:
        unique_together = (("content_type", "object_pk", "key"),)
        db_table = 'django_expando'

class ExpandoModel(models.Model):

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        skip_expando_fields = kwargs.pop('skip_expando_fields', False)

        r = super(ExpandoModel, self).save(*args, **kwargs)

        if not skip_expando_fields:
            assert self.pk

            Expando.objects.delete_for_object(self)

            attrs = set(self.__dict__)
            fields = set(f.name for f in self._meta.fields)
            for key in attrs - fields:
                if not key.startswith('_') and not key.endswith('_id'):
                    Expando.objects.set_for_key(self, key)

        return r

    def _load_expando_fields(self):
        if not hasattr(self, '_expando_fields_cache'):
            qs = Expando.objects.get_for_object(self).order_by('id')
            self._expando_fields_cache = dict(qs.values_list('key', 'value'))
                                
    def __getattr__(self, key):
        if not key.startswith('_') and self.pk:
            try:
                self._load_expando_fields()
                return self._expando_fields_cache[key]
            except KeyError:
                raise AttributeError("There is neither regular field nor "
                                     "expando field '%s' for %s" % (key, self))
        else:
            raise AttributeError("'%s' has no attribute '%s'" % (self, key))

    def get_expando_fields(self):
        self._load_expando_fields()
        return self._expando_fields_cache.copy()

def doctest():
    """
>>> import sys; print >>sys.stderr, "(Running expando_tests.)",

>>> from project_sample.expando_tests.models import ExpandoBasedModel

>>> # ExpandoBasedModel has single standard CharField 'existing_field'.

>>> o = ExpandoBasedModel(existing_field=2)
>>> o.existing_field
2
>>> o.strange_field
Traceback (most recent call last):
...
AttributeError: 'ExpandoBasedModel object' has no attribute 'strange_field'
>>> o.expando_field = 14
>>> o.save()
>>> del o

>>> o2 = ExpandoBasedModel.objects.get(existing_field='2') 
>>> o2.expando_field
u'14'
>>> o2.another_field
Traceback (most recent call last):
...
AttributeError: There is neither regular field nor expando field 'another_field' for ExpandoBasedModel object
>>> 
    """
