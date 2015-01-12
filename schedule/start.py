#!/usr/bin/env python

import os
import os.path
import functools
import subprocess

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


def start(security_groups, ssh_keyname):

    # FIXME create an ami from the provisioned instance. This will save us
    # from installing pip, awscli, etc all the time
    print(create_launch_configuration(launch_config, security_groups, ssh_keyname))
    print(create_auto_scaling_group(launch_config, auto_scale_group))
    suspend_processes(auto_scale_group)
    set_group_size(auto_scale_group, args.Quoted("Begin downtime check"), size=1,
                   recurrence=args.Quoted("0,15,30,45 * * * *"))
    set_group_size(auto_scale_group, args.Quoted("Finish downtime check"), size=0,
                   recurrence=args.Quoted("10,25,40,55 * * * *"))
    print("Add scheduled jobs")
    print(describe_scheduled_actions(auto_scale_group))
