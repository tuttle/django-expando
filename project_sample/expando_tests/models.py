from django.db import models
from django_expando.models import ExpandoModel

class ExpandoBasedModel(ExpandoModel):
    regular_field = models.CharField('Existing Field', max_length=32)

    def __unicode__(self):
        return u'ExpandoBasedModel(regular_field=%s)' % self.regular_field
