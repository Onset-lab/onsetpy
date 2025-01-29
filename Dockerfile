FROM python:3.10.15-slim-bullseye

# Install dependencies
RUN apt update; \
    apt install -y git jq

# Upgrade pip
RUN pip install --upgrade pip

# Install avnirpy
WORKDIR /
RUN git clone https://github.com/Onset-lab
WORKDIR /onsetpy
RUN pip install -e .

# Set entrypoint
ENTRYPOINT [""]