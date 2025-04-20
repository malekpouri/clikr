FROM ubuntu:latest
LABEL authors="alan"

ENTRYPOINT ["top", "-b"]