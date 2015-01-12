import json
import datetime
import itertools
from schedule.window import AWSInstance
from schedule.start import call, join


def partition(predicate, iterable):
    l1, l2 = itertools.tee((predicate(item), item) for item in iterable)
    return (i for p, i in l1 if p), (i for p, i in l2 if not p)


def describe_instances():
    return json.loads(call('ec2', 'describe-instances'))


def describe_instances_from_file(fname=None):
    fname = fname or join('instances.json')
    with open(fname) as fo:
        return json.load(fo)


def scheduled_instances(instances):
    """Filter instances where tag.Key == 'Scheduled'"""
    reservations = instances['Reservations']
    instances_ = []
    for res in reservations:
        ins = res['Instances']
        for instance in ins:
            tags = [t for t in instance['Tags'] if t['Key'] == 'Scheduled']
            if not tags:
                continue
            instances_.append(AWSInstance(instance))
    return instances_


def check():
    ids = list(scheduled_instances(describe_instances()))
    now = datetime.datetime.utcnow()
    pred = lambda win: now in win
    to_start, to_stop = map(list, partition(pred, ids))
    if to_stop:
        instance_ids = ' '.join([i.id for i in to_stop]),
        stopped = call('ec2', 'stop-instances', instance_ids=instance_ids)
    else:
        stopped = 'No instances to stop'

    if to_start:
        instance_ids = ' '.join([i.id for i in to_start])
        started = call('ec2', 'start-instances', instance_ids=instance_ids)
    else:
        started = 'No instances to start'
    return '{}\n{}'.format(started, stopped)
