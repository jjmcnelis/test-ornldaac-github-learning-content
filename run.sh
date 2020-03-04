#!/bin/bash

# GET THE PATH TO THIS BASH SCRIPT (FOR DOCKER MOUNT):
DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )

# RUN THE CONTAINER:
docker run \
  -v $DIR/repositories:/data/repositories \
  -v $DIR/tests:/data/tests \
  --rm -it ornldaac-github-tests
