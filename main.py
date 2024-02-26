from flask import Flask, make_response, redirect, request, jsonify, render_template, send_from_directory
import os
import dotenv
import requests
import datetime
import json
import threading
import nacl.signing
import nacl.encoding
import nacl.exceptions
import base58
import render
import hashlib
import random

app = Flask(__name__)
dotenv.load_dotenv()


DISCORD_WEBHOOK = os.getenv('DISCORD_WEBHOOK')
utc_now = datetime.datetime.utcnow()

# If votes file doesn't exist, create it
if not os.path.isfile('data/votes.json'):
    with open('data/votes.json', 'w') as file:
        json.dump([], file)


#Assets routes
@app.route('/assets/<path:path>')
def send_report(path):
    return send_from_directory('templates/assets', path)

@app.route('/assets/js/bundle.js')
def send_bundle():
    return send_from_directory('dist', 'bundle.js')

@app.route('/sitemap')
@app.route('/sitemap.xml')
def sitemap():
    # Remove all .html from sitemap
    with open('templates/sitemap.xml') as file:
        sitemap = file.read()

    sitemap = sitemap.replace('.html', '')
    return make_response(sitemap, 200, {'Content-Type': 'application/xml'})

@app.route('/favicon.png')
def faviconPNG():
    return send_from_directory('templates/assets/img', 'favicon.png')


# Main routes
@app.route('/')
def index():
    year = datetime.datetime.now().year
    
    
    info = get_vote_info()
    options = render.options(info["options"])

    enabled = info["enabled"]
    end = datetime.datetime.strptime(info["end"], "%Y-%m-%d")
    smallEnd = end.strftime("%Y-%m-%d")
    # Format as 2024-02-27T00:00:00Z
    unixEnd = end.strftime("%Y-%m-%dT00:00:00Z")

    if not hasStarted() or hasEnded():
        enabled = False    

    revote = "not" if not info["revote"] else ""
    if info["public"]:
        votes = render.votes()
    else:
        votes = ""

    return render_template('index.html',year=year,votes=votes, options=options,
                           current_vote=info["vote"], description=info["description"],
                           end=end,enabled=enabled, public=info["public"],
                           revote=revote, smallEnd=smallEnd,
                           unixEnd=unixEnd,ended=hasEnded(),
                           notStarted=not hasStarted(),starts=startTime().strftime("%Y-%m-%d") + " UTC")

@app.route('/<path:path>')
def catch_all(path):
    year = datetime.datetime.now().year
    # If file exists, load it
    if os.path.isfile('templates/' + path):
        return render_template(path, year=year)
    
    # Try with .html
    if os.path.isfile('templates/' + path + '.html'):
        return render_template(path + '.html', year=year)

    return render_template('404.html', year=year), 404

@app.route('/vote')
def vote():
    print('Voting')
    # Get args
    args = request.args
    # Convert to json
    data = args.to_dict()

    print(data)

    # Verify signature
    message = data["message"]
    signature = data["signature"]
    public_key = data["walletAddress"]
    percent = data["percent"]

    # Check if revote is enabled
    info = get_vote_info()
    if not info['revote']:
        with open('data/votes.json') as file:
            votes = json.load(file)
        for vote in votes:
            if vote["walletAddress"] == public_key:
                return render_template('revotes.html', year=datetime.datetime.now().year)

    # Make sure the voting is enabled and hasn't ended
    if not info['enabled']:
        return render_template('404.html', year=datetime.datetime.now().year)

    if hasEnded():
        return render_template('404.html', year=datetime.datetime.now().year)
    
    if not hasStarted():
        return render_template('404.html', year=datetime.datetime.now().year)

    # Verify signature
    try:
        # Decode base58 encoded strings
        public_key_bytes = base58.b58decode(public_key)
        signature_bytes = base58.b58decode(signature)
        message_bytes = message.encode('utf-8')

        # Verify the signature
        verify_key = nacl.signing.VerifyKey(public_key_bytes)
        verify_key.verify(message_bytes, signature_bytes)

        # Signature is valid
        data["verified"] = True
        
    except (nacl.exceptions.BadSignatureError, nacl.exceptions.CryptoError) as e:
        # Signature is invalid
        data["verified"] = False
    
    # Send message to discord
    send_discord_message(data)
    save_vote(data)

    vote_chart = ""
    if info['public']:
        vote_chart = render.votes()
    else:
        date = datetime.datetime.strptime(info['end'], "%Y-%m-%d")
        if date < datetime.datetime.now():
            vote_chart = render.votes()
        

    return render_template('success.html', year=datetime.datetime.now().year, vote=data["message"],percent=percent,signature=signature,votes=vote_chart)

def save_vote(data):
    # Load votes
    with open('data/votes.json') as file:
        votes = json.load(file)

    address = data["walletAddress"]
    # Remove old vote
    for vote in votes:
        if vote["walletAddress"] == address:
            votes.remove(vote)
    # Add new vote
    votes.append(data)

    # Save votes
    with open('data/votes.json', 'w') as file:
        json.dump(votes, file, indent=4)

def send_discord_message(data):
    text = f"New vote for `{data['message']}`"

    tokens = data['votes']
    # Convert to have commas
    tokens = "{:,}".format(int(tokens))
    
    # Define the message content
    message = {
        "embeds": [
            {
                "title": "New Vote",
                "description": text,
                "color": 65280 if data["verified"] else 16711680,
                "footer": {
                    "text": "Nathan.Woodburn/"
                },
                "fields": [
                    {
                        "name": "Wallet Address",
                        "value": '`'+data["walletAddress"]+'`'
                    },
                    {
                        "name": "Vote",
                        "value": '`'+data["message"]+'`'
                    },
                    {
                        "name": "Verified",
                        "value": "Yes" if data["verified"] else "No"
                    },
                    {
                        "name": "Signature",
                        "value": '`'+data["signature"]+'`'
                    },
                    {
                        "name": "Number of tokens",
                        "value": tokens
                    }
                ]
            }
        ]
    }

    # Send the message as a POST request to the webhook URL
    if DISCORD_WEBHOOK is not None:
        requests.post(DISCORD_WEBHOOK, data=json.dumps(message), headers={'Content-Type': 'application/json'})

@app.route('/votes')
def download():
    if 'walletAddress' in request.args:
        address = request.args['walletAddress']
        with open('data/votes.json') as file:
            votes = json.load(file)
        for vote in votes:
            if vote["walletAddress"] == address:
                return jsonify([vote])
        return jsonify([])



    info = get_vote_info()
    if not info['public']:
        end = datetime.datetime.strptime(info['end'], "%Y-%m-%d")
        if end > datetime.datetime.now():
            return render_template('blocked.html', year=datetime.datetime.now().year), 404


    resp = make_response(send_from_directory('data', 'votes.json'))
    # Set as json
    resp.headers['Content-Type'] = 'application/json'
    return resp


#region admin
@app.route('/login', methods=['POST'])
def login():
    # If account.json doesn't exist, create it
    if not os.path.isfile('data/account.json'):
    
        user = request.form['email']
        # Hash password
        password = request.form['password']
        hashed = hashlib.sha256(password.encode()).hexdigest()
        token = random.randint(100000, 999999)
        with open('data/account.json', 'w') as file:
            json.dump({'email': user, 'password': hashed, 'token': token}, file)
        resp = make_response(redirect('/admin'))
        resp.set_cookie('token', str(token))
        return resp            

    
    # Read account.json
    with open('data/account.json') as file:
        account = json.load(file)

    

    user = request.form['email']
    # Hash password
    password = request.form['password']
    hashed = hashlib.sha256(password.encode()).hexdigest()
    
    if user == account['email'] and hashed == account['password']:
        token = random.randint(100000, 999999)
        account['token'] = token
        with open('data/account.json', 'w') as file:
            json.dump(account, file)
        resp = make_response(redirect('/admin'))
        resp.set_cookie('token', str(token))
        return resp
    
    return redirect('/')

@app.route('/admin')
def admin():
    if not 'token' in request.cookies:
        return redirect('/login')
    with open('data/account.json') as file:
        account = json.load(file)
    if request.cookies['token'] != str(account['token']):
        return redirect('/login')
    
    info = get_vote_info()
    options = ','.join(info['options'])

    return render_template('admin.html', year=datetime.datetime.now().year, name=info['vote'],
                           description=info['description'], end=info['end'], start=info['start'],
                           enabled=info['enabled'], public=info['public'], revote=info['revote'], options=options)

@app.route('/admin', methods=['POST'])
def admin_post():
    if not 'token' in request.cookies:
        return redirect('/login')
    with open('data/account.json') as file:
        account = json.load(file)
    if request.cookies['token'] != str(account['token']):
        return redirect('/login')

    info = get_vote_info()

    info['vote'] = request.form['name']
    info['description'] = request.form['description']
    info['end'] = request.form['end']
    info['start'] = request.form['start']
    info['enabled'] = 'enabled' in request.form
    info['public'] = 'public' in request.form
    info['revote'] = 'revote' in request.form
    options = request.form['options']
    options = options.split(',')
    info['options'] = options

    with open('data/info.json', 'w') as file:
        json.dump(info, file)
    
    return redirect('/admin')

@app.route('/admin/clear')
def clear():
    if not 'token' in request.cookies:
        return redirect('/login')
    with open('data/account.json') as file:
        account = json.load(file)
    if request.cookies['token'] != str(account['token']):
        return redirect('/login')
    with open('data/votes.json', 'w') as file:
        json.dump([], file)
    return redirect('/admin')


#endregion

def get_vote_info():
    if not os.path.isfile('data/info.json'):
        end = datetime.datetime.now() + datetime.timedelta(days=7)
        end = end.strftime("%Y-%m-%d")
        start = datetime.datetime.now() - datetime.timedelta(days=7)
        start = start.strftime("%Y-%m-%d")
        with open('data/info.json', 'w') as file:
            json.dump({'vote': '','description':'', 'end': end,'start':start,'enabled': False, 'public': True, 'revote': True, 'options': []}, file)
    with open('data/info.json') as file:
        info = json.load(file)
    return info


# 404 catch all
@app.errorhandler(404)
def not_found(e):
    return render_template('404.html', year=datetime.datetime.now().year), 404


# Time helper functions
def timeLeft():
    info = get_vote_info()
    end = utc_now.strptime(info["end"], "%Y-%m-%d")
    left = end - utc_now
    print(left)
    return left

def endTime():
    info = get_vote_info()
    end = utc_now.strptime(info["end"], "%Y-%m-%d")
    return end

def startTime():
    info = get_vote_info()
    start = utc_now.strptime(info["start"], "%Y-%m-%d")
    return start

def hasStarted():
    start = startTime()
    if utc_now > start:
        return True
    return False

def hasEnded():
    end = endTime()
    if utc_now > end:
        return True
    return False



if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')