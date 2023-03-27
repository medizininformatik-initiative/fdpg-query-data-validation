FROM python:3.9.10-slim-buster

RUN apt-get update && apt-get install -y \
    git \
    libcairo2-dev \
    libpango1.0-dev \
    libgdk-pixbuf2.0-dev \
    texlive \
    texlive-latex-recommended \
    texlive-latex-extra \
    texlive-fonts-recommended \
    texlive-xetex \
    texlive-bibtex-extra \
    pandoc \
    pandoc-citeproc

RUN pip install --upgrade pylatex

WORKDIR /app

# Copy all the necessary files and directories to the container
COPY . /app
