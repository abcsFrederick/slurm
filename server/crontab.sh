#!/bin/bash

jobinfo=$(/usr/local/bin/squeue -j $1)
if [[ $jobinfo != *$1* ]]; then
  curl -X POST --header 'Content-Length: 0' http://localhost:8888/api/v1/slurm/update?crontabId=$2&slurmJobId=$1
fi
