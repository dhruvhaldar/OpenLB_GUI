# Source https://hub.docker.com/r/openeuler/openlb/tags
FROM openeuler/openlb:1.9.0-oe2403sp1

# Fix: Replace -march=native -mtune=native with portable flags
# This prevents illegal instruction errors when Docker runs on different host CPUs
RUN sed -i 's/-march=native -mtune=native/-march=x86-64 -mtune=generic/g' \
    /home/release-1.9.0/config.mk

ENV OLB_ROOT=/home/release-1.9.0
WORKDIR /workspace
