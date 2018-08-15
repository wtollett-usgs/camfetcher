#!/bin/sh

support/build.sh
if [ $? == 0 ]; then
    docker stop camfetcher
    docker rm camfetcher
    docker run \
        --restart=always \
        --detach=true \
        --mount type=bind,src=$HOME/hvocam,dst=/data \
        --env-file=$HOME/private/camfetcher.env \
        --log-driver json-file \
        --log-opt max-size=10m \
        --name camfetcher \
        camfetcher
else
    echo "Build failed, exiting."
fi
