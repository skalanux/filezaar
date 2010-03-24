#!/bin/bash

# Check number of arguments

EXPECTED_ARGS=2
E_BADARGS=65

if [ $# -ne $EXPECTED_ARGS ]
then
    echo "usage:"
    echo "\n"
    echo "$ sh setup.sh REMOTE_REPOSITORY_URI LOCAL_FILE_PATH"
    echo "\n"
    echo "REMOTE_REPOSITORY_URI: URI of your repository i.e.:"
    echo "file:///tmp/filezaar_repo"
    echo "\n"
    echo "LOCAL_FILE_PATH: Desired filepath for your local files i.e.:"
    echo "    /tmp/filezaar_local"

    exit $E_BADARGS
fi

/usr/bin/bzr init $1
/usr/bin/bzr co $1 $2
