#!/usr/bin/env python

import os
import json
import os.path
import datetime
import argparse
import functools
import itertools
import subprocess

from schedule import window
from schedule import args


def join(*args):
    _here = os.path.dirname(__file__)
    return os.path.abspath(os.path.join(_here, *args))


user_data = 'file://{}'.format(join('scheduler.sh'))
ami_id = u"ami-f0b11187"
instance_type = u"t2.micro"
region = u"eu-west-1"
zone = region + "a"
launch_config = u"scheduler-launch-config"
auto_scale_group = u"scheduler-auto-scale-group"


def resource_may_exist(fn):
    """Decorator to handle commands that fail due to attempting to create a resource that already exists"""
    @functools.wraps(fn)
    def inner(*args, **kwargs):
        response = fn(*args, **kwargs)
        resource = {'create_auto_scaling_group': auto_scale_group}.get(fn.__name__, launch_config)
        if response.startswith('A client error (AlreadyExists)'):
            response = "The resource '{}' already exists".format(resource)
        elif not response:
            response = "Created resource '{}'".format(resource)
        return response
    return inner


def cmd(kind, subcommand, **kwargs):
    args_ = args.dict_to_cli_args(kwargs)
    return u'aws {kind} {sub} {args}'.format(kind=kind, sub=subcommand, args=args_)


def call(kind, subcommand, **kwargs):
    _cmd = cmd(kind, subcommand, **kwargs)
    try:
        x = subprocess.check_output(_cmd, stderr=subprocess.STDOUT, shell=True)
    except subprocess.CalledProcessError as err:
        x = err.output
    return x.strip()


@resource_may_exist
def create_launch_configuration(name, security_groups, ssh_keyname):
    args = {
        'launch_configuration_name': name,
        'output': 'text',
        'security_groups': security_groups,
        'image_id': ami_id,
        'user_data': user_data,
        'instance_type': instance_type,
        'key_name': ssh_keyname,
        'iam_instance_profile': 'scheduler',
    }
    return call('autoscaling', 'create-launch-configuration', **args)


@resource_may_exist
def create_auto_scaling_group(launch_config_name, group_name):
    args = {
        'auto_scaling_group_name': group_name,
        'launch_configuration_name': launch_config_name,
        'output': 'text',
        'availability_zones': zone,
        'desired_capacity': 0,
        'min_size': 0,
        'max_size': 0,
    }
    return call('autoscaling', 'create-auto-scaling-group', **args)


def suspend_processes(group_name):
    args = {
        'auto_scaling_group_name': group_name,
        'scaling_processes': 'ReplaceUnhealthy',
    }
    return call('autoscaling', 'suspend-processes', **args)


def set_group_size(group_name, action_name, size, recurrence):
    args = {
        'auto_scaling_group_name': group_name,
        'scheduled_action_name': action_name,
        'min_size': size,
        'max_size': size,
        'recurrence': recurrence,
    }
    return call('autoscaling', 'put-scheduled-update-group-action', **args)


def describe_scheduled_actions(group_name):
    args = {
        'auto_scaling_group_name': group_name,
    }
    return call('autoscaling', 'describe-scheduled-actions', **args)


def describe_instances():
    return json.loads(call('ec2', 'describe-instances'))


def describe_instances_from_file(fname=None):
    fname = fname or join('instances.json')
    with open(fname) as fo:
        return json.load(fo)


def do_run_check(args):
    print(run_check())


def partition(predicate, iterable):
    l1, l2 = itertools.tee((predicate(item), item) for item in iterable)
    return (i for p, i in l1 if p), (i for p, i in l2 if not p)


def run_check():
    ids = list(window.scheduled_instances(describe_instances_from_file()))
    now = datetime.datetime.utcnow()
    pred = lambda win: now in win
    to_start, to_stop = map(list, partition(pred, ids))
    args = {
        'dry-run': '',
        'instance_ids': ' '.join([i.id for i in to_stop]),
    }
    if to_stop:
        stopped = call('ec2', 'stop-instances', **args)
    else:
        stopped = 'No instances to stop'

    if to_start:
        args['instance_ids'] = ' '.join([i.id for i in to_start])
        started = call('ec2', 'start-instances', **args)
    else:
        started = 'No instances to start'
    return '{}\n{}'.format(started, stopped)


def do_start(args):
    start(security_groups=args.groups, ssh_keyname=args.keyname)


def start(security_groups, ssh_keyname):

    # FIXME create an ami from the provisioned instance. This will save us
    # from installing pip, awscli, etc all the time
    print(create_launch_configuration(launch_config, security_groups, ssh_keyname))
    print(create_auto_scaling_group(launch_config, auto_scale_group, subnet_id='N/a'))
    suspend_processes(auto_scale_group)
    set_group_size(auto_scale_group, args.Quoted("Begin downtime check"), size=1,
                   recurrence=args.Quoted("0,15,30,45 * * * *"))
    set_group_size(auto_scale_group, args.Quoted("Finish downtime check"), size=0,
                   recurrence=args.Quoted("10,25,40,55 * * * *"))
    print("Add scheduled jobs")
    print(describe_scheduled_actions(auto_scale_group))


parser = argparse.ArgumentParser()
subparsers = parser.add_subparsers(help='sub-command help')
check_parser = subparsers.add_parser('check',
                                     help='Check if any running instances should be stopped')
check_parser.set_defaults(func=do_run_check)

start_parser = subparsers.add_parser('start',
                                     help='Create auto-scaling group')
start_parser.set_defaults(func=do_start)
start_parser.add_argument('--keyname', '-k', action='store', required=True)
start_parser.add_argument('--groups', '-g', action='store', required=True)

if __name__ == '__main__':
    arguments = parser.parse_args()
    arguments.func(arguments)
