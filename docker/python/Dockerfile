###########
# BUILDER #
###########

FROM python:3.11 as builder
WORKDIR /usr/src/app
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install system dependencies
RUN apt-get update && apt-get install -y netcat && apt-get install -y --no-install-recommends gcc

# install dependencies
RUN python -m pip install --progress-bar off --no-cache-dir --upgrade pip
# prepare all, including dev dependencies, to be cached
COPY ./requirements.txt /usr/src/app/requirements.txt
COPY ./requirements-dev.txt /usr/src/app/requirements-dev.txt
# this will create a wheel cache for all dependencies
RUN pip wheel --progress-bar off --no-cache-dir --wheel-dir /usr/src/app/wheels -r requirements.txt

##############
# BASE IMAGE #
##############
FROM python:3.11 as base
# create directory for the app user
RUN mkdir -p /home/app

# create the app user
RUN addgroup --system app && adduser --system --group app

# create the appropriate directories
ENV HOME=/home/app
ENV APP_HOME=/home/app/nlp4all
RUN mkdir $APP_HOME
WORKDIR $HOME

# install dependencies
RUN apt-get update && apt-get install -y --no-install-recommends netcat

# update pip
RUN pip install --upgrade pip

# install dependencies
COPY --from=builder /usr/src/app/wheels /wheels
COPY --from=builder /usr/src/app/requirements.txt .
RUN pip install --no-cache /wheels/*
COPY ./docker/python/entrypoint.sh $HOME
RUN chmod +x $HOME/entrypoint.sh
RUN chown -R app:app $HOME

##############
# PROD IMAGE #
##############
FROM base as nlpapp

COPY ./nlp4all $APP_HOME
# ensure correct ownership
RUN chown -R app:app $APP_HOME


# change to the app user
USER app

# run entrypoint.sh
ENTRYPOINT ["/home/app/entrypoint.sh"]


#############
# DEV IMAGE #
#############
FROM base as nlpapp-dev

# add dev requirements
COPY --from=builder /usr/src/app/requirements-dev.txt .
RUN pip install --progress-bar off --no-cache-dir -r requirements-dev.txt
# install debugpy for remote debug listening
RUN pip install debugpy

COPY ./docker/python/run-nlp4all.sh $HOME
RUN chmod +x $HOME/run-nlp4all.sh
RUN chown app:app $HOME/run-nlp4all.sh

# change to the app user
USER app

# run entrypoint.sh
ENTRYPOINT ["/home/app/entrypoint.sh"]

