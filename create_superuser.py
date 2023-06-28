from django.contrib.auth import get_user_model

import os

User = get_user_model()
User.objects.create_superuser(os.environ.get('DJANGO_SUPERUSER_USERNAME'), os.environ.get('DJANGO_SUPERUSER_EMAIL') , os.environ.get('DJANGO_SUPERUSER_PASSWORD'))

