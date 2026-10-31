#!/bin/zsh
# After run_all.sh: three-level and two-level fine-tuned from v4's weights (1 channel, so v4 loads as is)
cd "$(dirname "$0")"
until grep -q "ALL DONE" run_all.log; do sleep 20; done
V4=/Users/varunmatta/Drive/Varun/Projects/captcha_tester/models/captcha_cnn_v4.pt
for v in three binary; do
  [[ -f results/${v}_s0_init-v4.json ]] || PYTHONWARNINGS=ignore python3 -u step2_train.py $v 0 $V4 2>&1
done
PYTHONWARNINGS=ignore python3 -u step3_report.py > report.log 2>&1
echo EXTRA DONE
