#!/bin/sh

set -e

yoyo apply --database "$DB_SCHEMA"://"$DB_USER":"$DB_PASSWORD"@"$DB_HOST"/"$DB_NAME" src/db/migrations

exec "$@"
