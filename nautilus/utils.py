#!/usr/bin/env python
# coding=utf-8

import subprocess
import numpy as np

def job2command(job):
    context = subprocess.check_output(['kubectl', 'describe', 'jobs', job]).decode()
    context = [c for c in context.split('\n') if 'python' in c]
    assert(len(context) == 1)
    context = context[0]
    return context.strip()
def job2name(job):
    context = subprocess.check_output(['kubectl', 'describe', 'jobs', job]).decode()
    context = [c for c in context.split('\n') if c[:5] == 'Name:']
    assert(len(context) == 1)
    name = context[0].split()[-1]
    # name = 'test-'+name[3:]
    return name
def job2limits(job):
    context = subprocess.check_output(['kubectl', 'describe', 'jobs', job]).decode()
    context = [c for c in context.split('\n')]
    index_flag = [c.strip()=='Limits:' for c in context]
    index = np.argmax(index_flag)
    cpu_limit = int(context[index+1].split()[1].strip())
    memory_limit = int(context[index+2].split()[1].strip().strip('Gi'))
    gpu_limit = int(context[index+3].split()[1].strip())
    return cpu_limit, memory_limit, gpu_limit
def job2requests(job):
    context = subprocess.check_output(['kubectl', 'describe', 'jobs', job]).decode()
    context = [c for c in context.split('\n')]
    index_flag = [c.strip()=='Requests:' for c in context]
    index = np.argmax(index_flag)
    cpu_request = int(context[index+1].split()[1].strip())
    memory_request = int(context[index+2].split()[1].strip().strip('Gi'))
    gpu_request = int(context[index+3].split()[1].strip())
    return cpu_request, memory_request, gpu_request
def job2config(job, public_flag):
    name = job2name(job)
    command = job2command(job)
    cpu_limit, memory_limit, gpu_limit = job2limits(job)
    cpu_request, memory_request, gpu_request = job2requests(job)
    resources = {
        'cpu_limit':cpu_limit, 'memory_limit':memory_limit, 'gpu_limit':gpu_limit,
        'cpu_request':cpu_request, 'memory_request':memory_request, 'gpu_request':gpu_request,
    }
    config = get_config(name, public_flag, command, resources)
    return config

private_config = '''
      affinity:
        nodeAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
            nodeSelectorTerms:
              - matchExpressions:
                - key: nautilus.io/group
                  operator: In
                  values:
                  - haosu
'''

def run_config(name, public_flag, command, resources):
    config = get_config(name, public_flag, command, resources)
    with open('tmp.yaml', 'w') as f:
        f.write(config)
    subprocess.call(['kubectl', 'create', '-f', 'tmp.yaml'])

def get_config(name, public_flag, command, resources):
    config = '''
apiVersion: batch/v1
kind: Job
metadata:
  name: %s
  namespace: ucsd-haosulab
  labels:
    user: haotang # Specify your name
spec:
  ttlSecondsAfterFinished: 86400  # Wait one day to delete completed jobs
  template:
    spec:
%s
      tolerations:
      - effect: NoSchedule
        key: nautilus.io/haosu
        operator: Exists
      - effect: NoSchedule
        key: nautilus.io/suncave
        operator: Exists
      tolerations:
      - effect: NoSchedule
        key: nautilus.io/wave
        operator: Exists
      containers:
      - name: gpu-container
        image: silent56/main:run3.sh
        command:
        - "sh"
        args:
        - "-c"
        - "%s"
        resources:
          requests:
            cpu: "%d"
            memory: "%dGi"
            nvidia.com/gpu: %d
          limits:
            cpu: "%d"
            memory: "%dGi"
            nvidia.com/gpu: %d
        volumeMounts:
          - name: cephfs-vol
            mountPath: /cephfs-old
          - name: cephfs
            mountPath: /cephfs
          # - name: dshm
            # mountPath: /dev/shm
      volumes:
      # - name: dshm  # shared memory
        # emptyDir:
          # medium: Memory
      - name: cephfs
        persistentVolumeClaim:
            claimName: haosulab-cephfs
      - name: cephfs-vol  # shared filesystem
        flexVolume:
          driver: ceph.rook.io/rook
          fsType: ceph
          options:
            fsName: nautilusfs
            clusterNamespace: rook
            path: /ucsd-haosulab
            mountUser: ucsd-haosulab
            mountSecret: ceph-fs-secret
      restartPolicy: Never
  backoffLimit: 2
    '''%(
        name,
        '#' if public_flag else private_config,
        command,
        resources['cpu_request'], resources['memory_request'], resources['gpu_request'],
        resources['cpu_limit'], resources['memory_limit'], resources['gpu_limit'],
    )
    return config

