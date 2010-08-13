from django.utils.encoding import smart_unicode
from django.contrib.contenttypes.models import ContentType

from django_expando.models import Expando

def expando_filter(model_qs, **kwargs):
    """ Filters the query set of the model having expando fields based on the
        value of the expando field. See tests in django_expando.models for usage.
        TODO: Not very efficient and clever implementation...
    """
    for k,v in kwargs.items():
        try:
            k, lookup = k.split('__', 1)
            lookup = '__' + lookup
        except ValueError:
            lookup = ''

        v = smart_unicode(v)
        kw = { 'key': k, 'value' + lookup: v }
        pks_ = Expando.objects.filter(**kw).values_list('object_pk', flat=True)
        try:
            pks = pks & set(pks_)
        except UnboundLocalError:
            pks = set(pks_)

    return model_qs.filter(pk__in=pks)

def expando_distinct_values(model_class, field_name):
    """ Returns all possible values for a specific expando field.
        Useful for search forms widgets.
    """
    ct = ContentType.objects.get_for_model(model_class)
    qs = Expando.objects.filter(content_type=ct, key=field_name)
    return qs.distinct().values_list('value', flat=True)
