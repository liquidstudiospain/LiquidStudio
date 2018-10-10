#!/usr/local/bin/bash

while :
do
    # WAVE1
    ./querylog.sh DEBORA || exit 1
    ./querylog.sh ERNESTO || exit 1
    ./querylog.sh SONIA || exit 1
    ./querylog.sh TAMARA || exit 1
    # WAVE2
    ./querylog.sh PATRICIA || exit 1
    ./querylog.sh ALBERTO || exit 1
    ./querylog.sh MARIA || exit 1
    ./querylog.sh EDUARDO || exit 1
    # AUX
    ./querylog.sh INTEGRATION || exit 1
done
