import time
import datetime


class AWSInstance(object):
    def __init__(self, instance):
        self.id = instance['InstanceId']


class ELB(object):
    def __init__(self, **kwargs):
        self.name = kwargs['LoadBalancerName']
        self.instances = [AWSInstance(i) for i in kwargs['Instances']]

    @property
    def instance_ids(self):
        return [i.id for i in self.instances]

    def __repr__(self):
        return u'<{}.{} {}>'.format(self.__module__, self.__class__.__name__,
                                    self.name)


class AWSScheduledInstance(object):
    def __init__(self, instance, schedule):
        self.id = instance['InstanceId']
        self.state = instance['State'].values()
        self.on, self.off = xx(schedule)

    def __contains__(self, other):
        return active_window(other, self._on, self._off)

    @property
    def on(self):
        return self._on.time()

    @on.setter
    def on(self, value):
        self._on = value

    @property
    def off(self):
        return self._off.time()

    @off.setter
    def off(self, value):
        self._off = value

    def __repr__(self):
        return u'<{} - on:{!r} off:{!r}>'.format(self.id, self.on, self.off)


def active_window(now, start, end):
    return start < now < end


def yy(s):
    tm = time.strptime(s, '%H.%M')
    # this works while we are only considering time and ignoring dates
    now = datetime.datetime.utcnow()
    return now.replace(second=0, microsecond=0, minute=tm.tm_min, hour=tm.tm_hour)


def xx(schedule_str):
    values = [x.split(':')[1] for x in schedule_str.split()]
    return [yy(c) for c in values]
