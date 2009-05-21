django-expando
==============

A reusable Django app allowing model attributes to be assigned dynamically
similar to App Engine's built-in expando class.

Current features:

* Not storing types: Any value is treated as string-like
* Transparent on-demand loading (when first unknown attr is accessed)
* Transparent saving on save()
* Enumerating as dict
* Basic filtering support
* Tests

See the tests in models.py for usage.

Note: This is early publication of the source. The project will gain the
usual sugar files and comments once the design and implementation matures.

Please forward any related thoughts to Vlada Macek <macek@sandbox.cz>,
greatly appreciated.

Thanks to Peter Baumgartner, http://www.lincolnloop.com, for savvy guidance
and sponsorship.


TODO
====

Investigate whether the DB index on UPPER("value") will help to improve the
performance of icontains. Possible, according to a quick experiment.
