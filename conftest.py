import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.testing")

import django

django.setup()
