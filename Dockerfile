# syntax=docker/dockerfile:1
FROM python:3.9 AS base

LABEL maintainer.name="Gabriel Lauzier"
LABEL maintainer.email="gabriel.lauzier@usherbrooke.ca"

ARG USER=clipy

ARG DEBIAN_FRONTEND=noninteractive

WORKDIR /app
ADD . /app/

RUN apt-get update -qq \
    && ln -sf /usr/share/zoneinfo/UTC /etc/localtime \
    # Install clipy and dev required packages
    && pip3 install --upgrade pip \
    && pip3 install --no-cache-dir -r requirements/dev-requirements.txt \
    && pip3 install --no-cache-dir -e . \
    # Clean cache
    && apt-get autoremove -y \
    && apt-get clean -y \
    && rm -rf /var/cache/apt/archives/* \
    && rm -rf /var/lib/apt/lists/* \
    && find / -type d -name '*__pychache__' -prune -exec rm -rf {} \; \
    # Create Python links if does not exist
    && if [[ ! -e /usr/bin/python ]]; then ln -sf /usr/bin/python3 /usr/bin/python; fi \
    && if [[ ! -e /usr/bin/python-config ]]; then ln -sf /usr/bin/python3-config /usr/bin/python-config; fi \
    && if [[ ! -e /usr/bin/pip ]]; then ln -sf /usr/bin/pip3 /usr/bin/pip; fi \
    # Add unprivileged user
    && groupadd --gid 10042 ${USER} \
    && useradd --uid 10042 --gid ${USER} -s /bin/bash --create-home ${USER}

USER 10042

CMD ["/bin/bash"]
