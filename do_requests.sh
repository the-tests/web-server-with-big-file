#!/usr/bin/env bash

while true
do
  TIME="$(curl -o /dev/null -s -w '%{time_total}\n' http://localhost:7777)"
  echo "$TIME * 1000" | bc -l
  #TIME=$((TIME * 1000))
  sleep 0.1
done
