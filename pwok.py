# coding=utf-8
import os
import requests
# from bs4 import BeautifulSoup
from grab import Grab
from flask import Flask, render_template, redirect, request, url_for
from flask_wtf import Form
from wtforms import StringField
from wtforms.validators import DataRequired, length, regexp
import datetime
from flask_shorturl import ShortUrl
from flask.ext.pymongo import PyMongo
from flask_pymongo import DESCENDING
from flask.ext.qrcode import QRcode
from urllib import parse

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['MONGO_DBNAME'] = 'links'

mongo = PyMongo(app)
su = ShortUrl(app)
QRcode(app)


class MyForm(Form):
    name = StringField('Enter your Long URL', validators=[
        DataRequired(message=u'this field is required'),
        length(max=2000, message=u'maximum URL length of 2000 characters'),
        length(min=10, message=u'minimum URL length of 10 characters'),
        regexp(r"(https?://|ftp://)", message=u'please enter a valid URL to \
        shorten')
    ])


@app.route('/', methods=('GET', 'POST'))
def home():
    form = MyForm()
    g = Grab()
    date_create = datetime.datetime.utcnow().strftime('%d, %b %Y %H:%M')
    date_for_sitemap = datetime.datetime.now().strftime('%Y-%m-%d')
    uid_number = mongo.db.short_url.find().count()
    uid_number += 1
    short = su.encode_url(uid_number)
    uid = su.decode_url(short)
    long_url = form.data['name']
    domain_parse = parse.urlparse(long_url)
    domain = '{}://{}'.format(domain_parse.scheme, domain_parse.netloc)
    ip = request.headers.get('X-Real-IP')
    if form.validate_on_submit():
        # title_req = requests.get(long_url)
        try:
            title_req = g.go(long_url)
            soup_title = title_req.select("//title").text()
            soup_description = title_req.select(
                '//meta[@name="description"]/@content').text()
            # soup_keywords = title_req.select(
            #     '//meta[@name="keywords"]/@content').text()
        except IndexError:
            mongo.db.short_url.insert_one(
                {
                    'domain': domain,
                    'long_url': long_url,
                    'short_url': '{}{}'.format('http://pwok.pw/', short),
                    'date_create': date_create,
                    'date_for_sitemap': date_for_sitemap,
                    'clicks': int(0),
                    'uid': uid,
                    'views': int(0),
                    'title': soup_title,
                    'ip': ip
                    # 'description': soup_description,
                    # 'keywords': soup_keywords
                }
            )
        else:
            mongo.db.short_url.insert_one(
                {
                    'domain': domain,
                    'long_url': long_url,
                    'short_url': '{}{}'.format('http://pwok.pw/', short),
                    'date_create': date_create,
                    'date_for_sitemap': date_for_sitemap,
                    'clicks': int(0),
                    'uid': uid,
                    'views': int(0),
                    'title': soup_title,
                    'ip': ip,
                    'description': soup_description
                    # 'keywords': soup_keywords
                }
            )
        return redirect(url_for('.success'))
    return render_template('index.html', form=form, ip=ip)


@app.route('/success/', methods=('GET', 'POST'))
def success():
    if request.referrer == 'http://pwok.pw/':
        url = mongo.db.short_url.find().sort('_id', DESCENDING).limit(1)
        return render_template('success.html', url=url)
    return redirect('/')


@app.route('/<page>', methods=('GET', 'POST'))
def redirect_to_url(page):
    rd = '{}{}'.format('http://pwok.pw/', page)
    referrer = request.referrer
    user_agent = request.user_agent
    browser = user_agent.browser
    platform = user_agent.platform
    ip = request.headers.get('X-Real-IP')
    geo = requests.get('http://freegeoip.net/json/' + ip)
    data_geo = geo.json()
    country = data_geo['country_name']
    city = data_geo['city']
    for i in mongo.db.short_url.find():
        if rd == i['short_url']:
            mongo.db.short_url.update_one(
                {
                    'short_url': rd,
                    '$isolated': 1
                },
                {
                    '$inc': {'clicks': 1}
                }
            )
            mongo.db.short_url.update_one(
                {
                    'short_url': rd,
                    '$isolated': 1
                },
                {
                    '$push':
                        {
                            'referrer': referrer,
                            'browser': browser,
                            'platform': platform,
                            'country': country,
                            'city': city
                        }
                }
            )
            return redirect(i['long_url'])


@app.route('/success/<ObjectId:id>')
def show_task(id):
    task = mongo.db.short_url.find_one_or_404(id)
    stat = '{}{}'.format('http://pwok.pw/success/', id)
    referrer = mongo.db.short_url.aggregate([
        {'$match': {'_id': id}},
        {'$group': {'_id': "$_id", 'referrer': {'$addToSet': "$referrer"}}},
        {'$unwind': "$referrer"}, {'$unwind': "$referrer"},
        {'$group': {'_id': "$referrer", 'count': {'$sum': 1}}}])
    browser = mongo.db.short_url.aggregate([
        {'$match': {'_id': id}},
        {'$group': {'_id': "$_id", 'browser': {'$addToSet': "$browser"}}},
        {'$unwind': "$browser"}, {'$unwind': "$browser"},
        {'$group': {'_id': "$browser", 'count': {'$sum': 1}}}])
    platform = mongo.db.short_url.aggregate([
        {'$match': {'_id': id}},
        {'$group': {'_id': "$_id", 'platform': {'$addToSet': "$platform"}}},
        {'$unwind': "$platform"}, {'$unwind': "$platform"},
        {'$group': {'_id': "$platform", 'count': {'$sum': 1}}}])
    country = mongo.db.short_url.aggregate([
        {'$match': {'_id': id}},
        {'$group': {'_id': "$_id", 'country': {'$addToSet': "$country"}}},
        {'$unwind': "$country"}, {'$unwind': "$country"},
        {'$group': {'_id': "$country", 'count': {'$sum': 1}}}])
    city = mongo.db.short_url.aggregate([
        {'$match': {'_id': id}},
        {'$group': {'_id': "$_id", 'city': {'$addToSet': "$city"}}},
        {'$unwind': "$city"}, {'$unwind': "$city"},
        {'$group': {'_id': "$city", 'count': {'$sum': 1}}}])
    mongo.db.short_url.update_one({'_id': id, '$isolated': 1},
                                  {'$inc': {'views': 1}})
    return render_template('statistics.html', stat=stat, task=task,
                           mongo=mongo, referrer=referrer, browser=browser,
                           platform=platform, country=country, city=city)


@app.route('/sitemap/')
def sitemap():
    return render_template('sitemap.xml', mongo=mongo)

if __name__ == '__main__':
    app.run()
