import json
import datetime
import itertools
from schedule.window import (is_running, is_stopped,
                             create_aws_instance_if_scheduled)
from schedule.start import call, join
from schedule.start import region as default_region


def partition(predicate, iterable):
    l1, l2 = itertools.tee((predicate(item), item) for item in iterable)
    return (i for p, i in l1 if p), (i for p, i in l2 if not p)


def describe_instances(region, instance_ids=None):
    kw = {'region': region}
    if instance_ids:
        kw['instance_ids'] = instance_ids
    return json.loads(call('ec2', 'describe-instances', **kw))


def describe_instances_from_file(fname=None):
    fname = fname or join('instances.json')
    with open(fname) as fo:
        return json.load(fo)


def scheduled_instances(instances, creator=None):
    """Filter instances where tag.Key == 'Scheduled'"""
    creator = creator or create_aws_instance_if_scheduled
    reservations = instances['Reservations']
    instances_ = []
    for res in reservations:
        ins = res['Instances']
        for instance in ins:
            aws_instance = creator(instance)
            if aws_instance:
                instances_.append(aws_instance)
    return instances_


def check(region=None, ids=None):
    region = region or default_region
    if ids is None:
        ids = list(scheduled_instances(describe_instances(region)))
    now = datetime.datetime.utcnow()
    pred = lambda win: now in win

    to_start, to_stop = partition(pred, ids)
    to_stop = [i for i in to_stop if not is_stopped(i)]
    to_start = [i for i in to_start if not is_running(i)]

    if to_stop:
        instance_ids = ' '.join([i.id for i in to_stop])
        stopped = call('ec2', 'stop-instances', region=region, instance_ids=instance_ids)
    else:
        stopped = 'No instances to stop'

    if to_start:
        instance_ids = ' '.join([i.id for i in to_start])
        started = call('ec2', 'start-instances', region=region, instance_ids=instance_ids)
    else:
        started = 'No instances to start'
    return '{} | {}'.format(started, stopped)
