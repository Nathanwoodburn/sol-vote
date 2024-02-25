import json


def votes():
    # Load votes
    with open('data/votes.json') as file:
        votes = json.load(file)

    print(votes)

    options = {}
    for vote in votes:
        # Check if message is json
        if 'votes' not in vote:
            continue
        weight = int(vote["votes"]) / 100
        if vote["message"].startswith("{"):
            message = json.loads(vote["message"])
            for key in message:
                if key in options:
                    options[key] += (int(message[key]) * weight)
                else:
                    options[key] = (int(message[key]) * weight)
            continue
        if vote["message"] in options:
            options[vote["message"]] += weight * 100
        else:
            options[vote["message"]] = weight * 100

    
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
    html = '<select id="vote" class="form-select" name="vote" onchange="showHideDiv()" style="margin-bottom: 25px;">'
    for option in options:
        html += f'<option value="{option}">{option}</option>'

    # html += '<option value="Advanced">Mixed Vote</option>'
    html += '</select>'
    # Add a toggle to show/hide the advanced options
    html += '<label for="advancedToggle" style="display: inline;margin-left:10px;">Split Vote</label>'
    html += '<input type="checkbox" id="advancedToggle" name="advancedToggle" onchange="showHideDiv()">'


    html += f'''
    <script>function showHideDiv() {{
        var toggle = document.getElementById("advancedToggle");
        var divToToggle = document.getElementById("advancedOptions");
        if (toggle.checked) {{
            divToToggle.style.display = "block";
            // Set select to disabled
            document.querySelector('#vote').disabled = true;


        }} else {{
            divToToggle.style.display = "none";
            document.querySelector('#vote').disabled = false;
            // Set value of all inputs to 0
            var inputs = document.querySelectorAll('#advancedOptions input[type="number"]');
            inputs.forEach(function(input) {{
                input.value = 0;
            }});
            // Set value of matching select to 100
            var selectedValue = document.querySelector('#vote').value;
            var select = document.querySelector('#advancedOptions input[name="' + selectedValue + '"]');
            select.value = 100;
        }}
        }}
    </script>
    '''
    

    html += '<div id="advancedOptions" style="display: none;margin-top: 25px;text-align: left;">'
    for option in options:
        html += '<div class="form-group" style="margin-bottom: 10px;">'
        html += f'<label for="{option}" style="display: inline;margin-right:10px;">{option}</label>'
        value = 0
        if option == options[0]:
            value = 100

        html += f'<input id="{option}" type="number" name="{option}" value="{value}" class="form-control" style="width: auto; display: inline;margin-right:10px;" min="0" max="100" onchange="updateTotal()">'
        html += '% of vote share<br>'

        html += '</div>'    

    # Add a readonly input to show the remaining vote share
    html += '<div class="form-group" style="margin-bottom: 10px;">'
    html += '<p style="display:inline;">Remaining </p>'
    html += f'<p style="display:inline;" id="remaining">0</p>'
    html += '<p style="display:inline;">% of vote share</p>'

    html += '</div>'
    
    

    html += f'''
    <script>
        function updateTotal() {{
            var inputs = document.querySelectorAll('#advancedOptions input[type="number"]');
            var sum = 0;

            inputs.forEach(function(input) {{
                sum += parseInt(input.value);
            }});
            var remaining = 100 - sum;
            document.getElementById("remaining").innerText = remaining;
        }}
    </script>    
    '''

    return html