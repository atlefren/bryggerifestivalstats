# -*- coding: utf-8 -*-

import os
import requests
import json

CLIENT_ID = os.environ['CLIENT_ID']
CLIENT_SECRET = os.environ['CLIENT_SECRET']


def get(url):
    r = requests.get(url)
    return r.json()


def get_data(url, filename):
    checkins = []
    max_id = 0
    while max_id is not None:
        d = get(url + '&max_id=%s' % max_id)
        if d['meta']['code'] == 500:
            print 'Error, id=%s' % max_id
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


def _url_params():
    return 'client_id=%s&client_secret=%s' % (CLIENT_ID, CLIENT_SECRET)


def _get(url):
    print 'FETCHING DATA FROM UNTAPPD:\n%s' % url
    data = requests.get(url).json()
    if data['meta']['code'] == 500:
        msg = data['meta']['error_detail']
        raise Exception(msg)
    return data


def get_checkins_user(user):
    params = (user, _url_params())
    url = 'https://api.untappd.com/v4/user/checkins/%s?%s&limit=100' % params
    json = _get(url)

    checkins = json['response']['checkins']['items']
    next = json['response']['pagination']['next_url']
    while next:
        next += '&' + _url_params()
        next += '&limit=100'
        print next
        json = _get(next)
        checkins += json['response']['checkins']['items']
        next = json['response']['pagination']['next_url']

    return checkins


def save(data, filename):
    with open(filename, 'w') as outfile:
        outfile.write(json.dumps(data, indent=4))


def get_data_for_user(username, filename):
    save(get_checkins_user(username), filename)


def get_data_for_venue(venue_id, filename):
    url = 'https://api.untappd.com/v4/venue/checkins/%s?client_id=%s&client_secret=%s' % (venue_id, CLIENT_ID, CLIENT_SECRET)
    get_data(url, filename)


if __name__ == '__main__':
    # get_data_for_venue('912196', 'run4.json')
    get_data_for_user('martinp', 'martinp.json')
