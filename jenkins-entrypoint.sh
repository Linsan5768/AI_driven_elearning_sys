#!/bin/bash
# Fix Docker socket permissions on startup (need root privileges)
if [ -S /var/run/docker.sock ]; then
    chmod 666 /var/run/docker.sock 2>/dev/null || true
fi

# Start Jenkins (this will switch to jenkins user internally)
exec /usr/local/bin/jenkins.sh "$@"

