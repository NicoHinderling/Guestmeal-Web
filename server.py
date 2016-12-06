import datetime
import json
import os
import requests
import urllib

# from dotenv import Dotenv
from flask import Flask, redirect, render_template, \
    request, send_from_directory, session
from functools import wraps
from gevent.wsgi import WSGIServer
from werkzeug.debug import DebuggedApplication
from werkzeug.serving import run_with_reloader

# Custom Files
from authwrapper import auth0Wrapper
from database import BensKillerDatabase
from send_grid import ClientMail

auth0 = auth0Wrapper()
database = BensKillerDatabase()
emailClient = ClientMail()

# env = Dotenv('./.env')
env = os.environ

app = Flask(__name__, static_url_path='')
app.secret_key = env['SECRET_KEY']
app.debug = False

# Requires authentication annotation
def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'profile' not in session:
            return redirect('/')
        return f(*args, **kwargs)
    return decorated

# Controllers API
@app.route('/')
def index():
    ### For later: Making the homepage recognize that you're already logged in
    '''
    if 'profile' not in session:
        return render_template('index.html', env=env, user=None)
    else:
        return render_template('index.html', env=env, user=session['profile'])
    '''
    price = {}
    # PRICE Variables:
    # ----------------
    #   current_price: The current value of our lowest bid (pre-computed based on the current time)
    #   rate_of_decrease: The amount of milliseconds that this price should decrease by 1 cent
    #   time_left: The amount of milliseconds that this guestmeal is still available

    lowest_price = database.get_active_lowest_price()

    if lowest_price:
        seconds_left = ((lowest_price[1]['time'] + datetime.timedelta(hours=24)) - datetime.datetime.now()).total_seconds()
        cents_to_go = (lowest_price[0] - float(lowest_price[1]['min_price']))*100
        rate_of_decrease = (seconds_left/cents_to_go) * 1000

        price = {'current_price': lowest_price[0], 'rate_of_decrease': rate_of_decrease,
            'time_left': seconds_left * 1000, 'guestmeal_id': lowest_price[1]['uid']}

    return render_template('index.html', env=env, price=price, user=None)


@app.route('/buy', methods=['GET', 'POST'])
@requires_auth
def buy():
    price = {}
    # PRICE Variables:
    # ----------------
    #   current_price: The current value of our lowest bid (pre-computed based on the current time)
    #   rate_of_decrease: The amount of milliseconds that this price should decrease by 1 cent
    #   time_left: The amount of milliseconds that this guestmeal is still available

    lowest_price = database.get_active_lowest_price()

    if lowest_price:
        seconds_left = ((lowest_price[1]['time'] + datetime.timedelta(hours=24)) - datetime.datetime.now()).total_seconds()
        cents_to_go = (lowest_price[0] - float(lowest_price[1]['min_price']))*100
        rate_of_decrease = (seconds_left/cents_to_go) * 1000

        price = {'current_price': lowest_price[0], 'rate_of_decrease': rate_of_decrease,
            'time_left': seconds_left * 1000, 'guestmeal_id': lowest_price[1]['uid'],
            'seller': auth0.get_first_name_from_user_id(lowest_price[1]['uid'])}

    if request.method == "GET":
        return render_template('buy.html', env=env, price=price, user=session['profile'])
    else:
        if 'guestmeal_id' not in request.form:
            return render_template('buy.html', user=session['profile'],
                price=price, server_message='An error has occurred. Please try again.')
        else:
            auctioned_guestmeal_object = database.is_available(request.form['guestmeal_id'])
            if auctioned_guestmeal_object:
                sold_price = database.calculate_current_price(auctioned_guestmeal_object)

                # Create the transaction in the database, and send the emails
                database.create_transaction(session['profile']['user_id'],
                    auctioned_guestmeal_object['_id'], sold_price)

                # Send buyer and sellers their respective emails
                emailClient.send_transaction_emails(session['profile']['email'],
                    auth0.get_email_from_user_id(auctioned_guestmeal_object['uid']), sold_price)

                return redirect('/dashboard?{}'.format(urllib.urlencode({'server_message':
                    'Guestmeal successfully purchased! Check your email for more information.'})))
            else:
                return render_template('buy.html', user=session['profile'],
                    price=price, server_message='Unforunately that guestmeal is no longer available.')



@app.route('/sell', methods=['GET', 'POST'])
@requires_auth
def sell():
    if request.method == "GET":
        return render_template('sell.html', user=session['profile'], server_message=request.args.get('server_message'))
    else:
        if 'min-price' not in request.form:
            return render_template('sell.html', user=session['profile'], server_message='An error has occurred. Please try again')
        else:
            # Insert this new guestmeal into the Database
            database.insert_record(session['profile']['user_id'], request.form['min-price'])
            return redirect('/dashboard?{}'.format(urllib.urlencode({'server_message': 'Guestmeal successfully put on auction!'})))


@app.route('/dashboard')
@requires_auth
def dashboard():
    users = auth0.get_users()
    from pprint import pprint
    pprint(users)
    uid_to_name = {}
    for x in users:
        try:
            uid_to_name[x['user_id']] = x['user_metadata']['first_name']
        except KeyError:
            uid_to_name[x['user_id']] = x['name']

    transactions = database.get_list_transactions(session['profile']['user_id'])

    past_transcations = []
    for x in transactions:
        price = '{:,.2f}'.format(x['selling_price'])
        item = {'time': x['time'].strftime("%B %d, %Y at %I:%M %p"), 'price': price}
        if x['buyer'] == session['profile']['user_id']:
            item['transaction_type'] = "Purchase from"
            item['name'] = uid_to_name[x['seller']]
        else:
            item['transaction_type'] = "Sold to"
            item['name'] = uid_to_name[x['buyer']]

        past_transcations.append(item)

    if request.args.get('server_message'):
        server_message = request.args.get('server_message');
        return render_template('dashboard.html', user=session['profile'], server_message=server_message, transactions=past_transcations)

    return render_template('dashboard.html', user=session['profile'], server_message="", transactions=past_transcations)


@app.route('/public/<path:filename>')
def static_files(filename):
    return send_from_directory('./public', filename)


@app.route('/writeup')
def writeup():
    return send_from_directory('./writeup', 'writeup.pdf')

@app.route('/about')
def about():
    return render_template('about.html', env=env, price=None, user=None)


@app.route('/callback')
def callback_handling():
    code = request.args.get('code')
    json_header = {'content-type': 'application/json'}
    token_url = 'https://guestmealme.auth0.com/oauth/token'.format(domain=env['AUTH0_DOMAIN'])
    token_payload = {
        'client_id' : env['AUTH0_CLIENT_ID'],
        'client_secret' : env['AUTH0_CLIENT_SECRET'],
        'redirect_uri' : env['AUTH0_CALLBACK_URL'],
        'code' : code,
        'grant_type' : 'authorization_code'
    }

    token_info = requests.post(token_url, data=json.dumps(token_payload),
                               headers=json_header).json()
    user_url = 'https://guestmealme.auth0.com/userinfo?access_token={access_token}'.format(
        domain=env['AUTH0_DOMAIN'], access_token=token_info['access_token'])
    user_info = requests.get(user_url).json()
    session['profile'] = user_info
    return redirect('/dashboard')

################################################## LEFT OFF ON THIS
@app.route('/logout')
def logout():
    url_encoded_destination = urllib.urlencode({'returnTo': 'http://www.guestmeal.me'})
    return redirect("https://guestmealme.auth0.com/v2/logout?{}".format(url_encoded_destination), code=302)


# Werkzeug has a bug with HTML5 videos and pipes breaking, so we're using WSGI for now
@run_with_reloader
def run_server():
    http_server = WSGIServer(('', int(os.environ.get('PORT', 3000))), DebuggedApplication(app))
    http_server.serve_forever()

if __name__ == "__main__":
    run_server()

