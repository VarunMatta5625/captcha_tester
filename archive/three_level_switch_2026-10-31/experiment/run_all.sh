#!/bin/zsh
# Runs every variant x seed in sequence (one GPU job at a time); log -> run_all.log
cd "$(dirname "$0")"
for seed in 0 1; do
  for v in binary three raw; do
    [[ -f results/${v}_s${seed}.json ]] && continue
    PYTHONWARNINGS=ignore python3 -u step2_train.py $v $seed 2>&1
  done
done
echo ALL DONE
