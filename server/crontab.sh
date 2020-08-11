#!/bin/bash

jobinfo=$(/usr/local/bin/squeue -j $1)
if [[ $jobinfo != *$1* ]]; then
  curl -X POST --header 'Content-Length: 0' "http://localhost:8888/api/v1/slurm/update?slurmJobId=$1&commentId=$2"
else
  curl -X PUT --header 'Content-Length: 0' "http://localhost:8888/api/v1/slurm/updatestep?slurmJobId=$1"
fi
