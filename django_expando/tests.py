from django.db import models
from django_expando.models import ExpandoModel

class SomeReferencedModel(models.Model):
    int_field = models.IntegerField()

class ExpandoBasedTestModel(ExpandoModel):
    """
>>> import sys; print >>sys.stderr, "(Running expando_tests.)",
>>> from django_expando import Expando
>>> # ExpandoBasedTestModel has single standard CharField 'regular_field'.

>>> o = ExpandoBasedTestModel(regular_field=2)
>>> print o
ExpandoBasedTestModel(regular_field=2, regular_fk=None)
>>> o.regular_field
2
>>> o.strange_field
Traceback (most recent call last):
...
AttributeError: ExpandoBasedTestModel has no attribute 'strange_field'
>>> o.ef1 = 14
>>> o.save()
>>> del o

>>> o2 = ExpandoBasedTestModel.objects.get(regular_field='2') 
>>> o2.ef1
u'14'
>>> o2.another_field
Traceback (most recent call last):
...
AttributeError: There is neither regular field nor expando field 'another_field' for ExpandoBasedTestModel
>>> o2.ef2 = 20
>>> o2.ef1
u'14'
>>> o2.save()
>>> del o2

>>> o3 = ExpandoBasedTestModel.objects.get(regular_field='2')
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

>>> o4 = ExpandoBasedTestModel.objects.get(regular_field='2')
>>> o4.ef3 = 'Hello World'
>>> o4.save()
>>> o4.get_expando_fields()
{'ef1': u'13', 'ef2': u'20', 'ef3': 'Hello World'}

>>> o5 = ExpandoBasedTestModel.objects.get(regular_field='2')
>>> o5.get_expando_fields()
{'ef1': u'13', 'ef2': u'20', 'ef3': u'Hello World'}
>>> del o5

>>> o6 = ExpandoBasedTestModel.objects.get(regular_field='2')
>>> del o6.ef2
>>> o6.save()
>>> del o6

>>> o7 = ExpandoBasedTestModel.objects.get(regular_field='2')
>>> o7.save()

>>> p = ExpandoBasedTestModel(regular_field=3, regular_fk=None)
>>> p.ef1 = 9
>>> p.save()
>>> del p

>>> from django_expando import expando_filter, expando_distinct_values

>>> qs = ExpandoBasedTestModel.objects.all()
>>> qs
[<ExpandoBasedTestModel: ExpandoBasedTestModel(regular_field=2, regular_fk=None)>, <ExpandoBasedTestModel: ExpandoBasedTestModel(regular_field=3, regular_fk=None)>]
>>> expando_filter(qs, ef1=9)
[<ExpandoBasedTestModel: ExpandoBasedTestModel(regular_field=3, regular_fk=None)>]
>>> expando_filter(qs, ef1=13)
[<ExpandoBasedTestModel: ExpandoBasedTestModel(regular_field=2, regular_fk=None)>]
>>> expando_filter(qs, ef1=100)
[]
>>> expando_filter(qs, ef100=100011)
[]

>>> expando_filter(qs, ef3='Hello World')
[<ExpandoBasedTestModel: ExpandoBasedTestModel(regular_field=2, regular_fk=None)>]
>>> expando_filter(qs, ef3='hello world')
[]
>>> expando_filter(qs, ef3__iexact='hello world')
[<ExpandoBasedTestModel: ExpandoBasedTestModel(regular_field=2, regular_fk=None)>]
>>> expando_filter(qs, ef3__istartswith='hello')
[<ExpandoBasedTestModel: ExpandoBasedTestModel(regular_field=2, regular_fk=None)>]

>>> for v in Expando.objects.values(): print "%(object_pk)r, %(id)r %(key)r: %(value)r, " % v
u'1', 1 u'ef1': u'13', 
u'1', 3 u'ef3': u'Hello World', 
u'2', 4 u'ef1': u'9', 

>>> expando_distinct_values(ExpandoBasedTestModel, 'ef1')
[u'13', u'9']
    """
    regular_field = models.CharField('Existing Field', max_length=32)
    regular_fk = models.ForeignKey(SomeReferencedModel, null=True)

    def __unicode__(self):
        return u'ExpandoBasedTestModel(regular_field=%s, regular_fk=%r)' % (self.regular_field, self.regular_fk)
        
