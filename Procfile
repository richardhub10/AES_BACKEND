web: python manage.py migrate --noinput && gunicorn ua_clinic_backend.wsgi:application --chdir backend --bind 0.0.0.0:$PORT
