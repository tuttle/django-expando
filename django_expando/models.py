from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.utils.encoding import smart_unicode

class ExpandoManager(models.Manager):
    def get_for_object(self, object):
        return self.model.objects.filter(
            content_type = ContentType.objects.get_for_model(object),
            object_pk = smart_unicode(object.pk)
        )

    def get_for_key(self, object, key):
        return self.get_for_object(object).get(key=key).value

    def set_for_key(self, object, key):
        value = object.__dict__[key]
        try:
            e = self.get_for_key(object, key)
            e.value = value
        except Expando.DoesNotExist:
            e = self.model(
                content_type = ContentType.objects.get_for_model(object),
                object_pk = smart_unicode(object.pk),
                key = key,
                value = value
            )
        e.save()

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

    def save(self, force_insert=False, force_update=False):
        super(ExpandoModel, self).save(force_insert, force_update)

        assert self.id
        attrs = set(self.__dict__)
        fields = set(f.name for f in self._meta.fields)
        for key in attrs - fields:
            if not key.startswith('_'):
                Expando.objects.set_for_key(self, key)
                                
    def _get_expando_value(self, key):
        if not hasattr(self, '_expando_values'):
            qs = Expando.objects.get_for_object(self)
            self._expando_values = dict( qs.values_list('key', 'value') )
        return self._expando_values[key]

    def __getattr__(self, key):
        if not key.startswith('_') and self.id:
            try:
                return self._get_expando_value(key)
            except KeyError:
                raise AttributeError("There is neither regular field nor "
                                     "expando field '%s' for %s" % (key, self))
        else:
            raise AttributeError("'%s' has no attribute '%s'" % (self, key))

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
