# -*- coding: utf-8 -*-

import os
import requests
import json
from dateutil.parser import parse
from collections import defaultdict
import jinja2

CLIENT_ID = os.environ['CLIENT_ID']
CLIENT_SECRET = os.environ['CLIENT_SECRET']

DIRECTORY = os.path.dirname(os.path.realpath(__file__))


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
        except Exception:
            break

    print 'got %s checkins' % len(checkins)

    with open(filename, 'w') as outfile:
        outfile.write(json.dumps(checkins, indent=4))


class Checkin(object):

    def __init__(self, data):
        self.data = data
        self.beer = data['beer']
        self.beer['brewery'] = data['brewery']
        self.brewery = data['brewery']
        self.user = data['user']

    def date(self):
        return parse(self.data['created_at'])


class Stats(object):

    def __init__(self, checkins):
        self.checkins = checkins
        self._get_stats()

    def _get_stats(self):
        beercheckins = defaultdict(list)
        brewerycheckins = defaultdict(list)
        usercheckins = defaultdict(list)
        for checkin in self.checkins:
            beercheckins[checkin.beer['bid']].append(checkin)
            brewerycheckins[checkin.brewery['brewery_id']].append(
                checkin.brewery
            )
            usercheckins[checkin.user['uid']].append(checkin.user)

        beers = []
        for key, beerlist in beercheckins.items():
            beer = beerlist[0].beer
            beer['num'] = len(beerlist)
            beer['score'] = sum([checkin.data['rating_score'] for checkin in beerlist]) / len(beerlist)
            #for checkin in beerlist:
            #    print checkin.data['rating_score']
            beers.append(beer)
        self.beers = sorted(beers, key=lambda beer: beer['num'], reverse=True)

        breweries = []
        for key, brewerylist in brewerycheckins.items():
            brewerylist[0]['num'] = len(brewerylist)
            breweries.append(brewerylist[0])
        self.breweries = sorted(breweries, key=lambda brewery: brewery['num'], reverse=True)

        users = []
        for key, userlist in usercheckins.items():
            userlist[0]['num'] = len(userlist)
            users.append(userlist[0])
        self.users = sorted(users, key=lambda user: user['num'], reverse=True)

    def _sorted(self):
        return sorted(self.checkins, key=lambda checkin: checkin.date())

    def year(self):
        return self.checkins[0].date().year

    def num(self):
        return len(self.checkins)

    def first(self):
        return self._sorted()[0].date()

    def last(self):
        return self._sorted()[-1].date()

    def beers_by_score(self):
        return sorted(self.beers, key=lambda beer: beer['score'], reverse=True)


def generate_stats(checkins):
    year_stats = defaultdict(list)

    checkins = [Checkin(checkin) for checkin in checkins]

    for checkin in checkins:
        year_stats[checkin.date().year].append(checkin)

    years = []
    for checkins in year_stats.values():
        year = {}
        stat = Stats(checkins)
        print 'Year: %s' % stat.year()
        year['year'] = stat.year()
        print 'Num checkins: %s' % stat.num()
        year['num_checkins'] = stat.num()
        print 'First: %s' % stat.first()
        print 'Last: %s' % stat.last()
        print 'Num beers: %s' % len(stat.beers)
        year['num_beers'] = len(stat.beers)
        print 'Top 5 beers by checkins:'
        year['beer_top_5'] = []
        for beer in stat.beers[:5]:
            print '\t%s - %s (%s)' % (beer['brewery']['brewery_name'], beer['beer_name'], beer['num'])
            year['beer_top_5'].append({
                'brewery': beer['brewery']['brewery_name'],
                'beer': beer['beer_name'],
                'num': beer['num']
            })
        print 'Top 5 beers by score:'
        year['beer_top_5_score'] = []
        for beer in stat.beers_by_score()[:5]:
            print '\t%s - %s (%.2f / 5)' % (beer['brewery']['brewery_name'], beer['beer_name'], beer['score'])
            year['beer_top_5_score'].append({
                'brewery': beer['brewery']['brewery_name'],
                'beer': beer['beer_name'],
                'score': beer['score']
            })
        print 'Num breweries: %s' % len(stat.breweries)
        year['num_breweries'] = len(stat.breweries)
        print 'Top 5 breweries by checkins:'
        year['brewery_top_5'] = []
        for brewery in stat.breweries[:5]:
            print '\t%s (%s)' % (brewery['brewery_name'], brewery['num'])
            year['brewery_top_5'].append({
                'name': brewery['brewery_name'],
                'num': brewery['num']
            })
        print 'Num drinkes: %s' % len(stat.users)
        year['num_users'] = len(stat.users)
        print 'Top 5 drinkers by checkins:'
        year['user_top_5'] = []
        for drinker in stat.users[:5]:
            print '\t%s (%s)' % (drinker['user_name'], drinker['num'])
            year['user_top_5'].append({
                'name': drinker['user_name'],
                'num': drinker['num']
            })
        print '\n'
        years.append(year)

    return {'years': years}


def print_template(data):
    template_loader = jinja2.FileSystemLoader(searchpath=DIRECTORY)
    template_env = jinja2.Environment(loader=template_loader)
    template = template_env.get_template('template.html')
    output_html = template.render(data)
    with open('data.html', 'w') as outfile:
        outfile.write(output_html.encode('utf-8'))


if __name__ == '__main__':
    # get_data('912196', 'run2.json')

    with open('run2.json') as run2:
        checkins = json.loads(run2.read())
        data = generate_stats(checkins)
        print_template(data)
