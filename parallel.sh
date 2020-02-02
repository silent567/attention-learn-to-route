#!/bin/bash
for task in "$@"; do {
  $task &
} done

sleep 10
cnt=$(ps -aux | grep .py | grep -v defunct | grep -v parallel.sh | wc -c)
echo $cnt
while ((cnt > 0)); do 
	ps -aux | grep .py | grep -v defunct | grep -v parallel.sh |  echo
	ps -aux | grep .py | grep -v defunct | grep -v parallel.sh |  wc -c | echo
	sleep 60
	cnt=$(ps -aux | grep .py | grep -v defunct | grep -v parallel.sh | grep -v grep | wc -c)
	echo $cnt
done
