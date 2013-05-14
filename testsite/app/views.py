from flask import render_template, redirect, request, current_app, session, \
    flash, url_for
from flask.ext.security import LoginForm, current_user, login_required, \
    login_user
from flask.ext.social.utils import get_provider_or_404
from flask.ext.social.views import connect_handler

import geo_utils
import vote_utils

from . import app, db
from .models import User
from .tools import requires_auth

import random
import string

import pygeoip
gi = pygeoip.GeoIP('app/data/GeoLiteCity.dat', pygeoip.MEMORY_CACHE)

import psycopg2
conn = psycopg2.connect("dbname='gis' user='blackmad' host='localhost' password='xxx'")

@app.route('/')
def index():
    geoip = gi.record_by_addr(request.remote_addr)
    print geoip
    areas = []
    if geoip['country_code'] == 'US':
      areas = geo_utils.getNearestCounties(conn, geoip['latitude'], geoip['longitude'])
      print areas
    
    return render_template('index.html', total_users=User.query.count(), areas=areas)


@app.route('/login')
def login():
    if current_user.is_authenticated():
        return redirect(request.referrer or '/')

    return render_template('login.html', form=LoginForm())


@app.route('/editor/<areaid>')
def editor(areaid=None):
    return render_template('editor.html', areaid=areaid)

@app.route('/register', methods=['GET', 'POST'])
@app.route('/register/<provider_id>', methods=['GET', 'POST'])
def register(provider_id=None):
    print 'REGISTER'
    if current_user.is_authenticated():
        return redirect(request.referrer or '/')

    print 'HELLLLLLOOOOO'

    if provider_id:
        print provider_id
        provider = get_provider_or_404(provider_id)
        connection_values = session.get('failed_login_connection', None)
    else:
        provider = None
        connection_values = None
  
    print 'true?'
    print provider
    print connection_values
    if provider and connection_values:
        char_set = string.ascii_uppercase + string.digits
        ds = current_app.security.datastore
        user = ds.create_user(
          email=''.join(random.sample(char_set*32,32)) + '@test.com',
          password=''.join(random.sample(char_set*32,32))
        )
        user.api_key = ''.join(random.sample(char_set*32,32))

        ds.commit()

        # See if there was an attempted social login prior to registering
        # and if so use the provider connect_handler to save a connection
        connection_values = session.pop('failed_login_connection', None)

        if connection_values:
            connection_values['user_id'] = user.id
            connect_handler(connection_values, provider)

        if login_user(user):
            ds.commit()
            flash('Account created successfully', 'info')
            return redirect(url_for('profile'))

        return render_template('thanks.html', user=user)

    login_failed = int(request.args.get('login_failed', 0))

    return render_template('register.html',
                           provider=provider,
                           login_failed=login_failed,
                           connection_values=connection_values)


@app.route('/profile')
@login_required
def profile():
    areaids = vote_utils.getAreaIdsForUserId(conn, current_user.id)
    areas = geo_utils.getInfoForAreaIds(conn, areaids)
    return render_template('profile.html',
        areas=areas,
        twitter_conn=current_app.social.twitter.get_connection(),
        facebook_conn=current_app.social.facebook.get_connection(),
        github_conn=current_app.social.github.get_connection()
    )


@app.route('/admin')
@requires_auth
def admin():
    users = User.query.all()
    return render_template('admin.html', users=users)


@app.route('/admin/users/<user_id>', methods=['DELETE'])
@requires_auth
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash('User deleted successfully', 'info')
    return redirect(url_for('admin'))
