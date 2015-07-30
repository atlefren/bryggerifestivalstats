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

    def words(self):
        skip = ["", " ", u"alle", u"andre", u"arbeid", u"av", u"begge", u"bort", u"bra", u"bruke", u"da", u"denne", u"der", u"deres", u"det", u"din", u"disse", u"du", u"eller", u"en", u"ene", u"eneste", u"enhver", u"enn", u"er", u"et", u"folk", u"for", u"fordi", u"forsøke", u"fra", u"få", u"før", u"først", u"gjorde", u"gjøre", u"god", u"gå", u"ha", u"hadde", u"han", u"hans", u"hennes", u"her", u"hva", u"hvem", u"hver", u"hvilken", u"hvis", u"hvor", u"hvordan", u"hvorfor", u"i", u"ikke", u"inn", u"innen", u"kan", u"kunne", u"lage", u"lang", u"lik", u"like", u"makt", u"mange", u"med", u"meg", u"meget", u"men", u"mens", u"mer", u"mest", u"min", u"mye", u"må", u"måte", u"navn", u"nei", u"ny", u"nå", u"når", u"og", u"også", u"om", u"opp", u"oss", u"over", u"part", u"punkt", u"på", u"rett", u"riktig", u"samme", u"sant", u"si", u"siden", u"sist", u"skulle", u"slik", u"slutt", u"som", u"start", u"stille", u"så", u"tid", u"til", u"tilbake", u"tilstand", u"under", u"ut", u"uten", u"var", u"ved", u"verdi", u"vi", u"vil", u"ville", u"vite", u"vår", u"være", u"vært", u"å", u"a", u"about", u"above", u"after", u"again", u"against", u"all", u"am", u"an", u"and", u"any", u"are", u"aren't", u"as", u"at", u"be", u"because", u"been", u"before", u"being", u"below", u"between", u"both", u"but", u"by", u"can", u"cannot", u"can't", u"com", u"could", u"couldn't", u"did", u"didn't", u"do", u"does", u"doesn't", u"doing", u"don't", u"down", u"during", u"each", u"few", u"for", u"from", u"further", u"get", u"had", u"hadn't", u"has", u"hasn't", u"have", u"haven't", u"having", u"he", u"he'd", u"he'll", u"her", u"here", u"here's", u"hers", u"herself", u"he's", u"him", u"himself", u"his", u"how", u"how's", u"http", u"i", u"i'd", u"if", u"i'll", u"i'm", u"in", u"into", u"is", u"isn't", u"it", u"its", u"it's", u"itself", u"i've", u"just", u"let's", u"like", u"me", u"more", u"most", u"mustn't", u"my", u"myself", u"no", u"nor", u"not", u"of", u"off", u"on", u"once", u"only", u"or", u"other", u"ought", u"our", u"ours ", u"ourselves", u"out", u"over", u"own", u"r", u"same", u"shan't", u"she", u"she'd", u"she'll", u"she's", u"should", u"shouldn't", u"so", u"some", u"such", u"than", u"that", u"that's", u"the", u"their", u"theirs", u"them", u"themselves", u"then", u"there", u"there's", u"these", u"they", u"they'd", u"they'll", u"they're", u"they've", u"this", u"those", u"through", u"to", u"too", u"under", u"until", u"up", u"very", u"was", u"wasn't", u"we", u"we'd", u"we'll", u"were", u"we're", u"weren't", u"we've", u"what", u"what's", u"when", u"when's", u"where", u"where's", u"which", u"while", u"who", u"whom", u"who's", u"why", u"why's", u"with", u"won't", u"would", u"wouldn't", u"www", u"you", u"you'd", u"you'll", u"your", u"you're", u"yours", u"yourself", u"yourselves", u"you've", ]
        translation_table = dict.fromkeys(map(ord, '.,'), None)
        words = []
        for checkin in self.checkins:
            words += [word.translate(translation_table).lower().strip()
                      for word in checkin.data['checkin_comment'].split(' ')]
        words = [word for word in words if word not in skip]
        word_frequencies = defaultdict(int)
        for word in words:
            word_frequencies[word] += 1
        res = []
        for word, count in word_frequencies.items():
            res.append([word, count * 4])
        return res



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
            'beer_bottom_5_score': stat.beers_by_score()[::-1][:5],
            'num_breweries': len(stat.breweries),
            'brewery_top_5': stat.breweries[:5],
            'num_users': len(stat.users),
            'user_top_5': stat.users[:5],
            'photos': stat.photos(),
            'pos': json.dumps(get_positions(stat.breweries)),
            'date_stats': stat.hours(),
            'words': json.dumps(stat.words())
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
    with open('data2.html', 'w') as outfile:
        outfile.write(output_html.encode('utf-8'))


if __name__ == '__main__':
        checkins = load_checkins('atlefren.json')
        data = generate_stats(checkins)
        print_template(data)
