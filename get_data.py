# -*- coding: utf-8 -*-

import os
import requests
import json

requests.packages.urllib3.disable_warnings()

CLIENT_ID = os.environ['CLIENT_ID']
CLIENT_SECRET = os.environ['CLIENT_SECRET']


def get(url):
    r = requests.get(url)
    return r.json()


def _get(url):
    print 'FETCHING DATA FROM UNTAPPD:\n' + url
    data = requests.get(url).json()
    if data['meta']['code'] == 500:
        msg = data['meta']['error_detail']
        raise Exception(msg)
    return data


def _url_params():
    return 'client_id=%s&client_secret=%s' % (CLIENT_ID, CLIENT_SECRET)


def get_next(response):
    pagination = response['response'].get('pagination', None)
    if pagination:
        return pagination['next_url']
    return None


def get_checkins(checkin_type, id):
    params = (checkin_type, id, _url_params())
    url = 'https://api.untappd.com/v4/%s/checkins/%s?%s&limit=100' % params
    # url += '&max_id=208783463'
    json = _get(url)

    checkins = json['response']['checkins']['items']
    next = get_next(json)
    while next:
        next += '&' + _url_params()
        next += '&limit=100'
        try:
            json = _get(next)
            new = json['response']['checkins']['items']
            print len(new)
            checkins += new
            next = get_next(json)
            print len(checkins)
        except Exception, e:
            print e
            break
    return checkins


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

    data = get_checkins('user', username)
    save(data, filename)


def get_data_for_venue(venue_id, filename):
    data = get_checkins('venue', venue_id)
    save(data, filename)


if __name__ == '__main__':
    get_data_for_venue('3327343', '20152.json')
    # get_data_for_user('atlefren', 'atlefren.json')
