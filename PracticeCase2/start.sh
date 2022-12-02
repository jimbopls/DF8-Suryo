#!/usr/bin/env bash

docker compose build .

docker compose up airflow-init

docker compose up
