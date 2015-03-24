import argparse
from schedule.check import check
from schedule import log as logging


logger = logging.getLogger('schedule.app')
logging.setup_logging()


def do_check(args):
    logger.info(check(region=args.region))


parser = argparse.ArgumentParser()
subparsers = parser.add_subparsers(help='sub-command help')
check_parser = subparsers.add_parser('check',
                                     help='Check if any running instances should be stopped')
check_parser.add_argument('--region', '-r', action='store')
check_parser.set_defaults(func=do_check)


if __name__ == '__main__':
    arguments = parser.parse_args()
    arguments.func(arguments)
