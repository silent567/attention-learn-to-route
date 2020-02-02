#!/usr/bin/env python
# coding=utf-8

import subprocess
import sys, random
random.seed(0)

with open('job_list.txt') as f:
    commands = f.readlines()
commands = [cmd.strip() for cmd in commands]
random.shuffle(commands)
# commands = list(zip(commands[::2], commands[1::2]))
commands = list(zip(commands))

for cmd in commands:
    subprocess.call(['python', 'run.py']+list(cmd)+list(sys.argv[1:]))
