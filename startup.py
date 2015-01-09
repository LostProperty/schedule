#!/usr/bin/env python

import os
import sys
import json
import os.path
import datetime
import functools
import subprocess


def join(*args):
    _here = os.path.dirname(__file__)
    return os.path.abspath(os.path.join(_here, *args))


user_data = 'file://{}'.format(join('scheduler.sh'))
ami_id = u"ami-f0b11187"
instance_type = u"t2.micro"
security_groups = u"SSH"
region = u"eu-west-1"
zone = region + "a"
launch_config = u"scheduler-launch-config"
auto_scale_group = u"scheduler-auto-scale-group"
key_name = 'lostproperty'


class Quoted(object):

    def __init__(self, st):
        self.st = st

    def __str__(self):
        return repr(self.st)


class KeyValue(object):
    def __init__(self, **kwargs):
        self.key_values = kwargs

    def __repr__(self):
        return reduce(lambda i, x: '{} {}={}'.format(i, *x), reversed(self.key_values.items()), '')


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


def debug(cmdfn):
    def inner(*args, **kwargs):
        return u'echo ' + cmdfn(*args, **kwargs)
    return inner


def client_token(delim=6):
    date = datetime.datetime.utcnow().strftime('%Y-%m-%d')
    return u'{user}-{delim}-{date}'.format(user=os.environ['USER'], date=date, delim=delim)


def underscores_to_dashes(keys):
    return [key.replace('_', '-') for key in keys]


def dict_to_cli_args(di):
    args = dict(zip(underscores_to_dashes(di.keys()), di.values()))
    return reduce(lambda i, x: '{} --{} {}'.format(i, *x), reversed(args.items()), '')


def cmd(kind, subcommand, **kwargs):
    args = dict_to_cli_args(kwargs)
    return u'aws {kind} {sub} {args}'.format(kind=kind, sub=subcommand, args=args)


def call(kind, subcommand, **kwargs):
    _cmd = cmd(kind, subcommand, **kwargs)
    try:
        x = subprocess.check_output(_cmd, stderr=subprocess.STDOUT, shell=True)
    except subprocess.CalledProcessError as err:
        x = err.output
    return x.strip()


@resource_may_exist
def create_launch_configuration(name):
    args = {
        'launch_configuration_name': name,
        'output': 'text',
        'security_groups': security_groups,
        'image_id': ami_id,
        'user_data': user_data,
        'instance_type': instance_type,
        'key_name': key_name,
        'iam_instance_profile': 'scheduler',
    }
    return call('autoscaling', 'create-launch-configuration', **args)


@resource_may_exist
def create_auto_scaling_group(launch_config_name, group_name, subnet_id):
    args = {
        'auto_scaling_group_name': group_name,
        'launch_configuration_name': launch_config_name,
        'output': 'text',
        'availability_zones': zone,
        # 'vpc_zone_identifier': subnet_id,
        'desired_capacity': 0,
        'min_size': 0,
        'max_size': 1,
    }
    return call('autoscaling', 'create-auto-scaling-group', **args)


def run_instances():
    args = {
        'image_id': ami_id,
        'security_groups': security_groups,
        'instance_type': instance_type,
        'user_data': user_data,
        'instance_initiated_shutdown_behavior': 'stop',
        'key_name': key_name,
        'iam_instance_profile': KeyValue(Name='scheduler'),
        'placement': KeyValue(AvailabilityZone=zone),
        'count': 1,
        'output': 'text',
        'query': 'Instances[*].InstanceId',
        'client_token': client_token(),
    }
    return call('ec2', 'run-instances', **args)


def describe_instances(instance_id):
    args = {
        'instance_ids': instance_id,
    }
    response = call('ec2', 'describe-instances', **args)
    try:
        return json.loads(response)
    except ValueError:
        sys.exit("Describing instance failed: {!r}".format(response))


def suspend_processes(group_name):
    args = {
        'auto_scaling_group_name': group_name,
        'scaling_processes': 'ReplaceUnhealthy',
    }
    return call('autoscaling', 'suspend-processes', **args)


def attach_instances(group_name, instance_id):
    args = {
        'auto_scaling_group_name': group_name,
        'instance_ids': instance_id,
    }
    return call('autoscaling', 'attach-instances', **args)


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


def create_tags(instance_id, key='Name', value='scheduler'):
    args = {'resources': instance_id,
            'tags': 'Key={k},Value={v}'.format(k=key, v=value)}
    return call('ec2', 'create-tags', **args)


def get_ip_address(description):
    instance = description['Reservations'][0]['Instances'][0]
    try:
        retval = instance['PublicIpAddress']
    except KeyError:
        state_reason = instance.pop('StateReason', '')
        retval = 'Cannot determine ip: {State!r} {StateReason!r}'.format(StateReason=state_reason, **instance)
        sys.exit(retval)
    return retval


def get_subnet_id(description):
    return description['Reservations'][0]['Instances'][0]['NetworkInterfaces'][0]['SubnetId']


def main():

    # FIXME create an ami from the provisioned instance. This will save us
    # from installing pip, awscli, etc all the time

    # instance_id = run_instances()
    # description = describe_instances(instance_id)
    # ip = get_ip_address(description)
    # subnet_id = get_subnet_id(description)
    # print("Instance {} running on {}".format(instance_id, ip))
    # create_tags(instance_id)
    # print("Tagging instance {}".format(instance_id))
    print(create_launch_configuration(launch_config))
    print(create_auto_scaling_group(launch_config, auto_scale_group, subnet_id='N/a'))
    suspend_processes(auto_scale_group)
    # attach_instances(auto_scale_group, instance_id)
    # print("Attached instance to auto-scaling group")
    set_group_size(auto_scale_group, Quoted("Begin downtime check"), size=1,
                   recurrence=Quoted("0,15,30,45 * * * *"))
    set_group_size(auto_scale_group, Quoted("Finish downtime check"), size=0,
                   recurrence=Quoted("10,25,40,55 * * * *"))
    print("Add scheduled jobs")
    print(describe_scheduled_actions(auto_scale_group))


if __name__ == '__main__':
    main()
