#!/bin/bash

jobinfo=$(squeue -j $1)
echo $jobinfo
if [[ $jobinfo != *$1* ]]; then
  curl https://localhost:8888/
fi





