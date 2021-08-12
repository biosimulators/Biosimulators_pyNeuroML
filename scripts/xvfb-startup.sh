#!/bin/bash
set -e

exec 6>/tmp/display.log
Xvfb -displayfd 6 -ac -screen 0 "$XVFB_RES" -nolisten tcp $XVFB_ARGS &
XVFB_PROC=$!
sleep 1
set +e
"$@"
result=$?
kill $XVFB_PROC || true
exec 6>&-
exit $result
