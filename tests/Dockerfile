FROM mambaorg/micromamba:bookworm

# Set up the environment
USER root

RUN apt-get update -y \
    && apt-get upgrade -y \
    && apt-get install -y \
    gcc-12 \
    g++-12 \
    openmpi-bin \
    && rm -rf /var/lib/apt/lists/*

# RUN apt-get update && apt-get install -y binutils
# RUN find / -name strings 2>/dev/null
# RUN strings /usr/lib/x86_64-linux-gnu/libstdc++.so.6 | grep GLIBCXX

USER mambauser
