class Quoted(object):
    """Wraps a string value so that it will be quoted when used in str.format

    >>> import schedule.args
    >>> u'{}'.format("Example")
    u'Example'
    >>> u'{}'.format(schedule.args.Quoted("Example"))
    u"'Example'"

    This is useful for when creating args for awscli that need to be quoted

    >>> u'aws foo --name {}'.format(schedule.args.Quoted("space separated"))
    u"aws foo --name 'space separated'"
    >>> u'aws foo --name {}'.format("space separated")
    u'aws foo --name space separated'
    """

    def __init__(self, st):
        self.st = st

    def __str__(self):
        return repr(self.st)


def underscores_to_dashes(keys):
    return [key.replace('_', '-') for key in keys]


def dict_to_cli_args(di):
    """Convert the the key value pairs of a dict to long-form style cli args

    >>> import schedule.args
    >>> schedule.args.dict_to_cli_args({'some_arg': 'a-value'})
    ' --some-arg a-value'
    """
    args = dict(zip(underscores_to_dashes(di.keys()), di.values()))
    return reduce(lambda i, x: '{} --{} {}'.format(i, *x), reversed(args.items()), '')
