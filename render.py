import json


def votes():
    # Load votes
    with open('data/votes.json') as file:
        votes = json.load(file)

    print(votes)

    options = {}

    for vote in votes:
        # Check if message is json
        if vote["message"].startswith("{"):
            message = json.loads(vote["message"])
            for key in message:
                if key in options:
                    options[key] += (int(message[key]) * int(vote["votes"]))
                else:
                    options[key] = (int(message[key]) * int(vote["votes"]))
            continue
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

def options(options):
    html = '<select id="vote" class="form-select" name="vote" onchange="showHideDiv()">'
    for option in options:
        html += f'<option value="{option}">{option}</option>'

    html += '<option value="Advanced">Advanced</option>'
    html += '</select>'
    html += f'''
    <script>function showHideDiv() {{
        var selectedValue = document.getElementById("vote").value;
        var divToToggle = document.getElementById("advancedOptions");
        if (selectedValue === "Advanced") {{
            divToToggle.style.display = "block";
        }} else {{
            divToToggle.style.display = "none";
            // Set value of all inputs to 0
            var inputs = document.querySelectorAll('#advancedOptions input[type="number"]');
            inputs.forEach(function(input) {{
                input.value = 0;
            }});
            // Set value of matching select to 100
            var select = document.querySelector('#advancedOptions input[name="' + selectedValue + '"]');
            select.value = 100;
        }}
        }}
    </script>
    '''
    

    html += '<div id="advancedOptions" style="display: none;margin-top: 25px;text-align: left;">'
    lastOption = options[-1]
    for option in options:
        html += '<div class="form-group" style="margin-bottom: 10px;">'
        html += f'<label for="{option}" style="display: inline;margin-right:10px;">{option}</label>'
        value = 0
        if option == options[0]:
            value = 100

        if not lastOption == option:
            html += f'<input id="{option}" type="number" name="{option}" value="{value}" class="form-control" style="width: auto; display: inline;margin-right:10px;" min="0" max="100" onchange="updateLastInput()">'
            html += '% of vote share<br>'
        else:
            html += f'<input id="{option}" type="number" name="{option}" value="0" class="form-control" style="width: auto; display: inline;margin-right:10px;" min="0" max="100" readonly>'
            html += '% of vote share (automatically calculated)<br>'

        
        html += '</div>'    
    html += '</div>'


    html += f'''
    <script>
        function updateLastInput() {{
            var inputs = document.querySelectorAll('#advancedOptions input[type="number"]:not([readonly])');
            var sum = 0;

            inputs.forEach(function(input) {{
                sum += parseInt(input.value);
            }});

            var lastInput = document.getElementById('{lastOption}');
            lastInput.value = 100 - sum;
        }}
    </script>    
    '''

    return html