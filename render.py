import json


def votes():
    # Load votes
    with open('data/votes.json') as file:
        votes = json.load(file)


    options = {}
    for vote in votes:
        if vote["message"] in options:
            options[vote["message"]] += vote["votes"]
        else:
            options[vote["message"]] = vote["votes"]

    
    labels = list(options.keys())
    data = list(options.values())
    chart_data = {
        "type": "pie",
        "data": {
            "labels": labels,
            "datasets": [{
                "label": "Votes",
                "backgroundColor": ["rgb(17,255,69)", "rgb(255,0,0)", "rgb(0,0,255)", "rgb(255,255,0)", "rgb(255,0,255)", "rgb(0,255,255)", "rgb(128,0,128)"],
                "data": data
            }]
        },
        "options": {
            "maintainAspectRatio": True,
            "legend": {
                "display": True,
                "labels": {
                    "fontStyle": "normal"
                }
            },
            "title": {
                "fontStyle": "bold"
            }
        }
    }

    html = '<script src="assets/js/bs-init.js"></script>'
    html += f'<canvas data-bss-chart=\'{json.dumps(chart_data)}\' class="chartjs-render-monitor"></canvas>'

    return html