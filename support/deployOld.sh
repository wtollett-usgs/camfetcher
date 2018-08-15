support/build.sh
if [ $? == 0 ]; then
    docker stop camfetcher
    docker rm camfetcher
    docker run \
        --restart=always \
        --detach=true \
        --volume /lamp/cams:/cams \
        --env-file=/home/tparker/private/camfetcher.env \
        --name camfetcher \
        camfetcher
else
    echo "Build failed, exiting."
fi
