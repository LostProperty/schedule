import time
import datetime


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


class AWSInstance(object):
    def __init__(self, instance):
        self.id = instance['InstanceId']
        schedule = [t['Value'] for t in instance['Tags'] if t['Key'] == 'Scheduled'][0]
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
