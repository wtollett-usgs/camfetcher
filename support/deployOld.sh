support/build.sh
if [ $? == 0 ]; then
    docker stop camfetcher
    docker rm camfetcher
    docker run \
        --restart=always \
        --detach=true \
        --volume /lamp/cams:/cams \
        --env-file=/home/tparker/private/camfetcher.env \
        --log-driver json-file \
        --log-opt max-size=10m \
        --name camfetcher \
        camfetcher
else
    echo "Build failed, exiting."
fi
