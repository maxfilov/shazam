#!/bin/bash
curl -X POST 'localhost:8000/shazam' \
    -H 'cache-control: no-cache' \
    -H 'content-type: multipart/form-data' \
    -F "file=@$1" | jq 
