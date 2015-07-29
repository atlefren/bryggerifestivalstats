# -*- coding: utf-8 -*-

import os
import requests
import json

CLIENT_ID = os.environ['CLIENT_ID']
CLIENT_SECRET = os.environ['CLIENT_SECRET']


def get(url):
    r = requests.get(url)
    return r.json()


def get_data(venue_id, filename):
    checkins = []

    url = 'https://api.untappd.com/v4/venue/checkins/%s?client_id=%s&client_secret=%s' % (venue_id, CLIENT_ID, CLIENT_SECRET)

    max_id = 0
    while max_id is not None:
        d = get(url + '&max_id=%s' % max_id)
        if d['meta']['code'] == 500:
            print('Error, id=' % max_id)
            break
        checkins = checkins + d['response']['checkins']['items']
        try:
            max_id = d['response']['pagination'].get('max_id', None)
            print max_id
        except Exception:
            break

    print 'got %s checkins' % len(checkins)

    with open(filename, 'w') as outfile:
        outfile.write(json.dumps(checkins, indent=4))


if __name__ == '__main__':
    get_data('912196', 'run4.json')
