# -*- coding: utf-8 -*-

import os

import json
from dateutil.parser import parse
from collections import defaultdict
import jinja2


DIRECTORY = os.path.dirname(os.path.realpath(__file__))


class Checkin(object):

    def __init__(self, data):
        self.data = data
        self.beer = data['beer']
        self.beer['brewery'] = data['brewery']
        self.brewery = data['brewery']
        self.user = data['user']

    def date(self):
        return parse(self.data['created_at'])

    def has_media(self):
        return self.data['media']['count'] > 0

    def photos(self, size):
        return [it['photo'][size] for it in self.data['media']['items'] if it['photo']]


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
        sorted_score = sorted(self.beers, key=lambda beer: beer['score'], reverse=True)
        return [b for b in sorted_score if b['num'] > 1]

    def photos(self):
        with_photo = [c for c in self.checkins if c.has_media()]

        photos = []
        for wp in with_photo:
            if wp.has_media():
                photos += wp.photos('photo_img_sm')
        return photos


def generate_stats(checkins):

    seen = set()
    checkins = [c for c in checkins if c['checkin_id'] not in seen and not seen.add(c['checkin_id'])]

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
            year['beer_top_5'].append(beer)
        print 'Top 5 beers by score:'
        year['beer_top_5_score'] = []
        for beer in stat.beers_by_score()[:5]:
            print '\t%s - %s (%.2f / 5)' % (beer['brewery']['brewery_name'], beer['beer_name'], beer['score'])
            year['beer_top_5_score'].append(beer)
        print 'Num breweries: %s' % len(stat.breweries)
        year['num_breweries'] = len(stat.breweries)
        print 'Top 5 breweries by checkins:'
        year['brewery_top_5'] = []
        for brewery in stat.breweries[:5]:
            print '\t%s (%s)' % (brewery['brewery_name'], brewery['num'])
            year['brewery_top_5'].append(brewery)
        print 'Num drinkes: %s' % len(stat.users)
        year['num_users'] = len(stat.users)
        print 'Top 5 drinkers by checkins:'
        year['user_top_5'] = []
        for drinker in stat.users[:5]:
            print '\t%s (%s)' % (drinker['user_name'], drinker['num'])
            year['user_top_5'].append(drinker)
        print '\n'
        year['photos'] = stat.photos()
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
    with open('run3.json') as run2:
        checkins = json.loads(run2.read())
        data = generate_stats(checkins)
        print_template(data)
