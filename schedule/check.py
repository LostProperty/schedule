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


def get_target(region, ids=None, should_filter=True):

    class Target(object):
        def __init__(self, to_start, to_stop):
            if should_filter:
                self.to_stop = [i for i in to_stop if not is_stopped(i)]
                self.to_start = [i for i in to_start if not is_running(i)]
            else:
                self.to_stop = list(to_stop)
                self.to_start = list(to_start)

            self.ids_to_stop = [i.id for i in self.to_stop]
            self.ids_to_start = [i.id for i in self.to_start]

    if ids is None:
        ids = list(scheduled_instances(describe_instances(region)))
    now = datetime.datetime.utcnow()
    pred = lambda win: now in win
    to_start, to_stop = partition(pred, ids)
    return Target(to_start=to_start, to_stop=to_stop)


def set_instance_state(action, instance_ids, region=default_region, **kwargs):
    if action not in ['start', 'stop']:
        raise TypeError('action must be either "start" or "stop"')
    action = '{}-instances'.format(action)
    instance_ids = ' '.join(instance_ids)
    return call('ec2', action, region=region, instance_ids=instance_ids, **kwargs)


def check(region=default_region, ids=None):

    target = get_target(region, ids, should_filter=True)

    if target.to_stop:
        stopped = set_instance_state('stop', target.ids_to_stop)
    else:
        stopped = 'No instances to stop'

    if target.to_start:
        started = set_instance_state('start', target.ids_to_start)
    else:
        started = 'No instances to start'
    return '{} | {}'.format(started, stopped)
