from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.utils.encoding import smart_unicode

def is_valid_expando_field_name(name):
    return not name.startswith('_') and not name.endswith('_id')

class Expando(models.Model):
    content_type = models.ForeignKey(ContentType)
    object_pk    = models.TextField('object id', db_index=True)
    key          = models.CharField('expando key', max_length=32, db_index=True)
    value        = models.TextField('expando value', db_index=True)
    
    class Meta:
        unique_together = (('content_type', 'object_pk', 'key'),)
        db_table = 'django_expando'

    def __unicode__(self):
        return u'%s=%s, id=%d' % (self.key, self.value, self.id)

class ExpandoModel(models.Model):

    class Meta:
        abstract = True

    def get_expando_names(self):
        """ Returns the set of all attribute names that are expando in
            the instance (beyond regular fields).
        """
        attrs = set(n for n in self.__dict__ if is_valid_expando_field_name(n))
        fields = set(f.name for f in self._meta.fields)
        return attrs - fields

    def get_expando_qs(self):
        """ Gets the QuerySet of all expando fields for this instance.
        """
        ct = ContentType.objects.get_for_model(self)
        pk = smart_unicode(self._get_safe_pk())
        return Expando.objects.filter(content_type=ct, object_pk=pk)

    def save(self, *args, **kwargs):
        """ Saves the instance and all its expando fields (possible opt-out).
        """
        skip_expando_fields = kwargs.pop('skip_expando_fields', False)

        # Original save, assigns the primary key
        r = super(ExpandoModel, self).save(*args, **kwargs)

        if not skip_expando_fields:
            assert self._get_safe_pk()

            names, db_names = self.get_expando_names(), set()

            # For all expando fields in the db...
            for ef in self.get_expando_qs():

                # register their names...
                db_names.add(ef.key)
                if ef.key in self.__dict__:

                    # do they need update to db?
                    val = smart_unicode(self.__dict__[ef.key])
                    if val != ef.value:
                        ef.value = val
                        ef.save()
                else:
                    # or they were deleted in the instance?
                    ef.delete()

            ct = ContentType.objects.get_for_model(self)

            # Add all instance's expandos not present in the db.
            for key in names - db_names:
                Expando(
                    content_type = ct,
                    object_pk = smart_unicode(self._get_safe_pk()),
                    key = key,
                    value = smart_unicode(self.__dict__[key])
                ).save(force_insert=True)

        return r

    def load_expando_fields(self):
        """ Load all expando fields to instance only once.
            Override only those not yet present.
        """
        assert self._get_safe_pk()
        if '_expando_loaded' not in self.__dict__:
            for k, v in self.get_expando_qs().values_list('key', 'value'):
                if k not in self.__dict__:
                    self.__dict__[str(k)] = v
            self._expando_loaded = True

    def _get_safe_pk(self):
        """ Get primary key value without accessing __getattr__.
        """
        return self.__dict__.get(self._meta.pk.attname)

    def __getattr__(self, key):
        """ Loads expando fields from db on demand -- when trying to access
            first unknown attribute..
        """
#        import sys; print >>sys.stderr, "<GETATTR %s>" % key
        if is_valid_expando_field_name(key) and self._get_safe_pk():
            self.load_expando_fields()
            try:
                return self.__dict__[key]
            except KeyError:
                raise AttributeError("There is neither regular field nor "
                                     "expando field '%s' for %s" % (key, self))
        else:
            if hasattr(super(ExpandoModel, self), '__getattr__'):
                return super(ExpandoModel, self).__getattr__(key)
            else:
                raise AttributeError("'%s' has no attribute '%s'" % (self, key))

    def __setattr__(self, key, value):
        """ Needed to load expando fields now so save() properly detects
            the differences of the sets.
        """
#        import sys; print >>sys.stderr, "<setATTR %s>" % key
        if is_valid_expando_field_name(key) and self._get_safe_pk():
            self.load_expando_fields()
        super(ExpandoModel, self).__setattr__(key, value)

    def __delattr__(self, key):
        """ Needed to load expando fields now so save() properly detects
            the differences of the sets.
        """
#        import sys; print >>sys.stderr, "<delATTR %s>" % key
        if is_valid_expando_field_name(key) and self._get_safe_pk():
            self.load_expando_fields()
        super(ExpandoModel, self).__delattr__(key)

    def get_expando_fields(self):
        """ Returns the dict of all expando fields.
        """
        if self._get_safe_pk():
            self.load_expando_fields()
        return dict( (k, self.__dict__[k]) for k in self.get_expando_names() )

def doctest():
    """
>>> import sys; print >>sys.stderr, "(Running expando_tests.)",

>>> from project_sample.expando_tests.models import ExpandoBasedModel

>>> # ExpandoBasedModel has single standard CharField 'regular_field'.

>>> o = ExpandoBasedModel(regular_field=2)
>>> o.regular_field
2
>>> o.strange_field
Traceback (most recent call last):
...
AttributeError: 'ExpandoBasedModel(regular_field=2)' has no attribute 'strange_field'
>>> o.ef1 = 14
>>> o.save()
>>> del o

>>> o2 = ExpandoBasedModel.objects.get(regular_field='2') 
>>> o2.ef1
u'14'
>>> o2.another_field
Traceback (most recent call last):
...
AttributeError: There is neither regular field nor expando field 'another_field' for ExpandoBasedModel(regular_field=2)
>>> o2.ef2 = 20
>>> o2.ef1
u'14'
>>> o2.save()
>>> del o2

>>> o3 = ExpandoBasedModel.objects.get(regular_field='2')
>>> o3.ef2
u'20'
>>> o3.ef1
u'14'
>>> o3.get_expando_fields()
{'ef1': u'14', 'ef2': u'20'}
>>> o3.ef1 = 13
>>> o3.ef3 = 100
>>> o3.save()
>>> del o3

>>> o4 = ExpandoBasedModel.objects.get(regular_field='2')
>>> o4.ef3 = 'Hello World'
>>> o4.save()
>>> o4.get_expando_fields()
{'ef1': u'13', 'ef2': u'20', 'ef3': 'Hello World'}

>>> o5 = ExpandoBasedModel.objects.get(regular_field='2')
>>> o5.get_expando_fields()
{'ef1': u'13', 'ef2': u'20', 'ef3': u'Hello World'}
>>> del o5

>>> o6 = ExpandoBasedModel.objects.get(regular_field='2')
>>> del o6.ef2
>>> o6.save()
>>> del o6

>>> o7 = ExpandoBasedModel.objects.get(regular_field='2')
>>> o7.save()

>>> p = ExpandoBasedModel(regular_field=3)
>>> p.ef1 = 9
>>> p.save()
>>> del p

>>> from django_expando import expando_filter

>>> qs = ExpandoBasedModel.objects.all()
>>> expando_filter(qs, ef1=9)
[<ExpandoBasedModel: ExpandoBasedModel(regular_field=3)>]
>>> expando_filter(qs, ef1=13)
[<ExpandoBasedModel: ExpandoBasedModel(regular_field=2)>]
>>> expando_filter(qs, ef1=100)
[]
>>> expando_filter(qs, ef100=100011)
[]

>>> expando_filter(qs, ef3='Hello World')
[<ExpandoBasedModel: ExpandoBasedModel(regular_field=2)>]
>>> expando_filter(qs, ef3='hello world')
[]
>>> expando_filter(qs, ef3__iexact='hello world')
[<ExpandoBasedModel: ExpandoBasedModel(regular_field=2)>]
>>> expando_filter(qs, ef3__istartswith='hello')
[<ExpandoBasedModel: ExpandoBasedModel(regular_field=2)>]

>>> for v in Expando.objects.values(): print v
{'value': u'13', 'object_pk': u'1', 'id': 1, 'key': u'ef1', 'content_type_id': 3}
{'value': u'Hello World', 'object_pk': u'1', 'id': 3, 'key': u'ef3', 'content_type_id': 3}
{'value': u'9', 'object_pk': u'2', 'id': 4, 'key': u'ef1', 'content_type_id': 3}

    """
