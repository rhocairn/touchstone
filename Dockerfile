FROM debian:stretch AS py367

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



FROM py367 AS app

COPY ./src/py_ioc/__init__.py /app/src/py_ioc/
COPY ./src/py_ioc/version.py /app/src/py_ioc/
COPY ./setup.py /app/
RUN pip install -e /app[tests]
COPY . /app
WORKDIR /app
