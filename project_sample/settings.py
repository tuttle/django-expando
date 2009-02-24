# Django settings for project_sample project.
import os

PROJECT_DIR = os.path.abspath(os.path.dirname(__file__))

DEBUG = True
TEMPLATE_DEBUG = DEBUG

DATABASE_ENGINE = 'sqlite3'
DATABASE_NAME = 'django_expando_test_database.db'

SITE_ID = 1

ROOT_URLCONF = 'project_sample.nothing'

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.admin',
    'django.contrib.admindocs',
    'django_expando',
    'expando_tests',
)
