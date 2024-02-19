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

app = Flask(__name__)
dotenv.load_dotenv()


DISCORD_WEBHOOK = os.getenv('DISCORD_WEBHOOK')

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
    votes = render.votes()
    return render_template('index.html',year=year,votes=votes)

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
    return render_template('success.html', year=datetime.datetime.now().year, vote=data["message"],percent=percent,signature=signature,votes=render.votes())

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
    response = requests.post(DISCORD_WEBHOOK, data=json.dumps(message), headers={'Content-Type': 'application/json'})

    # Print the response from the webhook (for debugging purposes)
    print(response.text)

    

# 404 catch all
@app.errorhandler(404)
def not_found(e):
    return render_template('404.html', year=datetime.datetime.now().year), 404


if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')