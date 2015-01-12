class TestStateLookup(object):

    def test_simple_lookup(self):
        from schedule.window import AWS_INSTANCE_STATES
        assert AWS_INSTANCE_STATES.STOPPED == [80, 'stopped']

    def test_state_value_matches_dict_values(self):
        from schedule.window import AWS_INSTANCE_STATES
        di = {u'Code': 16, u'Name': u'running'}
        assert AWS_INSTANCE_STATES.RUNNING == di.values()
