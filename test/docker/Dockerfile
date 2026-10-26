# Probe-Image für die Selbstprüfung von docker-image.yml.
FROM mirror.gcr.io/library/busybox:1.37
ARG GRUSS
RUN echo "$GRUSS" > /gruss
CMD ["cat", "/gruss"]
