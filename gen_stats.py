# -*- coding: utf-8 -*-

import os
import math
import json
from dateutil.parser import parse
from collections import defaultdict
import jinja2

from datetime import timedelta

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
        return [it['photo'][size] for it
                in self.data['media']['items'] if it['photo']]


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
            score_sum = sum([checkin.data['rating_score']
                            for checkin in beerlist])
            beer['score'] = score_sum / len(beerlist)
            beers.append(beer)
        self.beers = sorted(beers, key=lambda beer: beer['num'], reverse=True)

        breweries = []
        for key, brewerylist in brewerycheckins.items():
            brewerylist[0]['num'] = len(brewerylist)
            breweries.append(brewerylist[0])
        self.breweries = sorted(
            breweries,
            key=lambda brewery: brewery['num'],
            reverse=True
        )

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
        sorted_score = sorted(
            self.beers,
            key=lambda beer: beer['score'],
            reverse=True
        )
        return [b for b in sorted_score if b['num'] > 1]

    def photos(self):
        with_photo = [c for c in self.checkins if c.has_media()]

        photos = []
        for wp in with_photo:
            if wp.has_media():
                photos += wp.photos('photo_img_sm')
        return photos

    def hours(self):

        times = [checkin.date() for checkin in self.checkins]

        start = min(times).replace(hour=0, minute=0, second=0, microsecond=0)

        days = math.ceil(
            (max(times) - start).total_seconds() / 60.0 / 60.0 / 24.0
        )

        series = []
        drilldowns = []
        for day in range(0, int(days)):
            day = start + timedelta(days=day)
            hours = [d for d in times
                     if d >= day and d < day + timedelta(days=1)]
            id = day.strftime('%d.%d')
            series.append({
                'name': day.strftime('%d. %b'),
                'y': len(hours),
                'drilldown': id,
            })
            drilldown_data = []
            for hour in range(0, 24):
                hour = day + timedelta(hours=hour)
                next_hour = hour + timedelta(hours=1)

                drilldown_data.append([
                    '%s - %s' % (
                        hour.strftime('%H.%M'),
                        next_hour.strftime('%H.%M')
                    ),
                    len([t for t in hours if t >= hour and t < next_hour])
                ])
            drilldowns.append({
                'data': drilldown_data,
                'name': id,
                'id': id
            })

        return {
            'series': series,
            'drilldowns': drilldowns
        }


def get_positions(breweries):
    features = []
    for brewery in breweries:
        if brewery['location'] is not None:
            has_lng = brewery['location']['lng'] != 0
            has_lat = brewery['location']['lat'] != 0
            if has_lat and has_lng:
                features.append({
                    "type": "Feature",
                    "properties": {"name": brewery['brewery_name']},
                    "geometry": {
                        "type": "Point",
                        "coordinates": [
                            brewery['location']['lng'],
                            brewery['location']['lat']
                        ]
                    }
                })
    return {
        "type": "FeatureCollection",
        "features": features
    }


def generate_stats(checkins):

    year_stats = defaultdict(list)
    checkins = [Checkin(checkin) for checkin in checkins]

    checkins = [c for c in checkins if c.date().month in [7, 8]]

    for checkin in checkins:
        year_stats[checkin.date().year].append(checkin)

    years = []
    for checkins in year_stats.values():
        stat = Stats(checkins)
        years.append({
            'year': stat.year(),
            'num_checkins': stat.num(),
            'num_beers': len(stat.beers),
            'beer_top_5': stat.beers[:5],
            'beer_top_5_score': stat.beers_by_score()[:5],
            'num_breweries': len(stat.breweries),
            'brewery_top_5': stat.breweries[:5],
            'num_users': len(stat.users),
            'user_top_5': stat.users[:5],
            'photos': stat.photos(),
            'pos': json.dumps(get_positions(stat.breweries)),
            'date_stats': stat.hours(),
        })
    return {'years': years}


def load_checkins(file):
    with open(file) as infile:
        checkins = json.loads(infile.read())
        seen = set()
        return [c for c in checkins if c['checkin_id']
                not in seen and not seen.add(c['checkin_id'])]


def print_template(data):
    template_loader = jinja2.FileSystemLoader(searchpath=DIRECTORY)
    template_env = jinja2.Environment(loader=template_loader)
    template = template_env.get_template('template.html')
    output_html = template.render(data)
    with open('data.html', 'w') as outfile:
        outfile.write(output_html.encode('utf-8'))


if __name__ == '__main__':
        checkins = load_checkins('run4.json')
        data = generate_stats(checkins)
        print_template(data)
