#!/bin/bash

jobinfo=$(/usr/local/bin/squeue -j $1)
if [[ $jobinfo != *$1* ]]; then
  echo "http://localhost:8888/api/v1/slurm/update?commentId=$2&slurmJobId=$1"
  curl -X POST --header 'Content-Length: 0' "http://localhost:8888/api/v1/slurm/update?commentId=$2&slurmJobId=$1"
fi
