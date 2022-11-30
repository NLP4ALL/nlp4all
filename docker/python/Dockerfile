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
COPY ./requirements.txt /usr/src/app/requirements.txt

RUN pip wheel --progress-bar off --no-cache-dir --wheel-dir /usr/src/app/wheels -r requirements.txt

#########
# FINAL #
#########
FROM python:3.11
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
COPY --from=builder /usr/src/app/wheels /wheels
COPY --from=builder /usr/src/app/requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache /wheels/*

COPY --from=builder /usr/src/app/wheels /wheels
COPY --from=builder /usr/src/app/requirements.txt .
COPY ./docker/python/entrypoint.sh $HOME
RUN chmod +x $HOME/entrypoint.sh

COPY ./nlp4all $APP_HOME

RUN chown -R app:app $HOME

# change to the app user
USER app

# run entrypoint.sh
ENTRYPOINT ["/home/app/entrypoint.sh"]