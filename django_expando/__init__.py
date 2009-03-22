from django_expando.models import Expando

def expando_filter(model_qs, **kwargs):
    """ Filters the query set of the model having expando fields based on the
        value of the expando field. See tests in django_expando.models for usage.
    """
    qs = Expando.objects
    for k,v in kwargs.items():
        try:
            k, lookup = k.split('__', 1)
            lookup = '__' + lookup
        except ValueError:
            lookup = ''

        qs = qs.filter(**{ 'key': k, 'value' + lookup: v })

    pks = qs.values_list('object_pk', flat=True)
    return model_qs.filter(pk__in=pks)

