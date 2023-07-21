
$(document).ready(function() {
  function initializeDataTable() {
    $("#datatable").DataTable();
    $(".dataTables_length select").addClass("form-select form-select-sm");
  }

  function fetchDataForChart() {
    return fetch('/get_chart_data/')
      .then(response => response.json())
      .then(data => {
        buildChart(data);
      })
      .catch(error => {
        console.error('ERROR CHARTS', error);
      });
  }

  function buildChart(chartData) {
    var options = {
      series: chartData.series,
      chart: {
        width: 380,
        type: 'pie'
      },
      labels: chartData.labels,
      responsive: [{
        breakpoint: 480,
        options: {
          chart: {
            width: 200
          },
          legend: {
            position: 'bottom'
          }
        }
      }]
    };
    var chart = new ApexCharts(document.querySelector("#balance-chart"), options);
    chart.render();
  }
  fetchDataForChart();
  initializeDataTable();
});
