# Base OS
FROM python:3.9-slim-buster

ARG VERSION=0.0.1
ARG SIMULATOR_VERSION="0.5.11"

# metadata
LABEL \
    org.opencontainers.image.title="pyNeuroML" \
    org.opencontainers.image.version="${SIMULATOR_VERSION}" \
    org.opencontainers.image.description="Python package for reading, writing, simulating and analysing NeuroML2/LEMS models" \
    org.opencontainers.image.url="https://github.com/NeuroML/pyNeuroML" \
    org.opencontainers.image.documentation="https://github.com/NeuroML/pyNeuroML/" \
    org.opencontainers.image.source="https://github.com/biosimulators/Biosimulators_pyNeuroML" \
    org.opencontainers.image.authors="BioSimulators Team <info@biosimulators.org>" \
    org.opencontainers.image.vendor="BioSimulators Team" \
    org.opencontainers.image.licenses="LGPL-3.0-only" \
    \
    base_image="python:3.9-slim-buster" \
    version="${VERSION}" \
    software="pyneuroml" \
    software.version="${SIMULATOR_VERSION}" \
    about.summary="Python package for reading, writing, simulating and analysing NeuroML2/LEMS models" \
    about.home="https://github.com/NeuroML/pyNeuroML" \
    about.documentation="https://github.com/NeuroML/pyNeuroML/" \
    about.license_file="https://raw.githubusercontent.com/NeuroML/pyNeuroML/master/LICENSE.lesser" \
    about.license="SPDX:LGPL-3.0-only" \
    about.tags="computational neuroscience,biochemical networks,dynamical modeling,stochastic simulation,NeuroML,SED-ML,COMBINE,OMEX,BioSimulators" \
    maintainer="BioSimulators Team <info@biosimulators.org>"

# Install requirements
RUN apt-get update -y \
    && apt-get install -y --no-install-recommends \
        openjdk-15-jre \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

# Copy code for command-line interface into image and install it
COPY . /root/Biosimulators_pyNeuroML
RUN pip install /root/Biosimulators_pyNeuroML \
    && rm -rf /root/Biosimulators_pyNeuroML
RUN pip install "pyneuroml==${SIMULATOR_VERSION}"
ENV VERBOSE=0 \
    MPLBACKEND=PDF

# Entrypoint
ENTRYPOINT ["pyneuroml"]
CMD []
