FROM python:3.8

ENV PYTHONUNBUFFERED 1

RUN mkdir /code
WORKDIR /code

COPY ./requirements.txt /requirements.txt

RUN pip install -r /requirements.txt

COPY ./mediators /mediators

COPY ./create_superuser.py /mediators/create_superuser.py

COPY ./entrypoint.sh /mediators/entrypoint.sh

WORKDIR /mediators

RUN python manage.py makemigrations
RUN python manage.py migrate

CMD ["/bin/sh", "entrypoint.sh"]