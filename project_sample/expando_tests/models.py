from django.db import models
from django_expando.models import ExpandoModel

class ExpandoBasedModel(ExpandoModel):
    existing_field = models.CharField('Existing Field', max_length=32)
