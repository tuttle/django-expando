import os
 
from distutils.core import setup
 
def fullsplit(path, result=None):
    """
    Split a pathname into components (the opposite of os.path.join) in a
    platform-neutral way.
    """
    if result is None:
        result = []
    head, tail = os.path.split(path)
    if head == "":
        return [tail] + result
    if head == path:
        return result
    return fullsplit(head, [tail] + result)
 
package_dir = "django_expando"
 
packages = []
for dirpath, dirnames, filenames in os.walk(package_dir):
    # ignore dirnames that start with '.'
    for i, dirname in enumerate(dirnames):
        if dirname.startswith("."):
            del dirnames[i]
    if "__init__.py" in filenames:
        packages.append(".".join(fullsplit(dirpath)))
 
setup(name='django_expando',
    version='0.1',
    description="A reusable Django app allowing model attributes to be assigned dynamically similar to App Engine's built-in expando class.",
    author='Vlada Macek',
    author_email='vlada@lincolnloop.com',
    url='https://github.com/tuttle/django-expando',
    packages=packages)