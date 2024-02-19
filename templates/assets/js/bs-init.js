document.addEventListener('DOMContentLoaded', function() {
    var charts = document.querySelectorAll('[data-bss-chart]');

    for (var chart of charts) {
        // Create the chart
        chart.chart = new Chart(chart, JSON.parse(chart.dataset.bssChart));
    }
}, false);

