FROM debian:stretch AS pythons

ENV PYENV_ROOT="/.pyenv" \
    PATH="/.pyenv/bin:/.pyenv/shims:$PATH"

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        ca-certificates \
        curl \
        git \
        libbz2-dev \
        libffi-dev \
        liblzma-dev \
        libncurses5-dev \
        libncursesw5-dev \
        libreadline-dev \
        libsqlite3-dev \
        libssl1.0-dev \
        llvm \
        make \
        python-openssl \
        tk-dev \
        wget \
        xz-utils \
        zip \
        zlib1g-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

RUN git clone https://github.com/pyenv/pyenv.git /.pyenv \
    && pyenv install 3.6.8 \
    && pyenv install 3.7.2 \
    && pyenv global $(pyenv versions --bare) \
    && pyenv rehash



FROM pythons AS app

COPY ./setup.py /app/
RUN mkdir -p /app/src/touchstone \
    && echo '__version__ = "0.0.1-dev1"' > /app/src/touchstone/version.py \
    && touch /app/README.md \
    && touch /app/src/touchstone/__init__.py \
    && pip install -e /app[tests,dist]

WORKDIR /app
COPY . /app
