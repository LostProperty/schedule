from schedule import wrappers


def get_scheduled_tag_value(instance):
    try:
        retval = [t['Value'] for t in instance['Tags'] if t['Key'] == 'Scheduled'][0]
    except IndexError:
        retval = ''
    return retval


def is_running(instance):
    return instance.state == AWS_INSTANCE_STATES.RUNNING


def is_stopped(instance):
    return instance.state == AWS_INSTANCE_STATES.STOPPED


def running_ids(instances):
    return [instance for instance in instances if is_running(instance)]


def stopped_ids(instances):
    return [instance for instance in instances if is_stopped(instance)]


# aws instance states
class AWS_INSTANCE_STATES:
    PENDING = [0, 'pending']
    RUNNING = [16, 'running']
    SHUTTING = [32, 'shutting-down']
    TERMINATED = [48, 'terminated']
    STOPPING = [64, 'stopping']
    STOPPED = [80, 'stopped']


def create_aws_instance_if_scheduled(instance):
    """Given the json version of an instance, create an AWSScheduledInstance wrapper"""
    schedule = get_scheduled_tag_value(instance)
    if not schedule:
        retval = None
    else:
        retval = wrappers.AWSScheduledInstance(instance, schedule)
    return retval
