from datetime import datetime
import pytz
import json
from gen_stats import Checkin


def read_json(filename):
    with open(filename, 'r') as inputfile:
        return json.loads(inputfile.read())


def write_json(data, filename):
    with open(filename, 'w') as outputfile:
        outputfile.write(json.dumps(data, indent=4))


def filter_checkins(checkins, min_date):
    return [c for c in checkins if Checkin(c).date() >= min_date]


if __name__ == '__main__':
    min_date = datetime(day=30, month=7, year=2015, tzinfo=pytz.utc)
    before = read_json('torvet.json')
    print len(before)
    after = filter_checkins(before, min_date)
    print len(after)
    write_json(after, 'torvet2.json')
