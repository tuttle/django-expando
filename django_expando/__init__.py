from django.utils.encoding import smart_unicode

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

