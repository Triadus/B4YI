$(document).ready(function () {

    function fetchDataForChart() {
        return fetch('/profit_chart_data/')
            .then(response => response.json())
            .then(data => {
                buildChart(data);
            })
            .catch(error => {
                console.error('ERROR CHARTS', error);
            });
    }

    function buildChart(chartData) {
        function getChartColorsArray(chartId) {
            if (document.getElementById(chartId) !== null) {
                var colors = document.getElementById(chartId).getAttribute("data-colors");
                if (colors) {
                    colors = JSON.parse(colors);
                    return colors.map(function (value) {
                        var newValue = value.replace(" ", "");
                        if (newValue.indexOf(",") === -1) {
                            var color = getComputedStyle(document.documentElement).getPropertyValue(newValue);
                            if (color) return color;
                            else return newValue;
                            ;
                        } else {
                            var val = value.split(',');
                            if (val.length == 2) {
                                var rgbaColor = getComputedStyle(document.documentElement).getPropertyValue(val[0]);
                                rgbaColor = "rgba(" + rgbaColor + "," + val[1] + ")";
                                return rgbaColor;
                            } else {
                                return newValue;
                            }
                        }
                    });
                }
            }
        }

        var overviewTimelineColors = getChartColorsArray("profit-chart-timeline");
        if (overviewTimelineColors) {
            var options = {
                series: [{
                    name: 'Profit',
                    data: chartData.series[0]
                }],
                chart: {
                    type: 'area',
                    height: 240,
                    toolbar: 'false'
                },
                dataLabels: {
                    enabled: false
                },
                stroke: {
                    curve: 'smooth',
                    width: 2,
                },
                markers: {
                    size: 0,
                    style: 'hollow',
                },
                xaxis: {
                    type: 'datetime',
                    tickAmount: 6,
                },
                tooltip: {
                    x: {
                        format: 'dd MMM yyyy'
                    }
                },
                yaxis: {
                    // min: 0,
                    tickAmount: 6,
                },

                labels: chartData.labels,
                colors: overviewTimelineColors,
                fill: {
                    type: 'gradient',
                    gradient: {
                        shadeIntensity: 1,
                        opacityFrom: 0.6,
                        opacityTo: 0.05,
                        stops: [42, 100, 100, 100]
                    }
                },
            };

            var chart = new ApexCharts(document.querySelector("#profit-chart-timeline"), options);
            chart.render();
        }

        var resetCssClasses = function (activeEl) {
            var els = document.querySelectorAll("button");
            Array.prototype.forEach.call(els, function (el) {
                el.classList.remove('active');
            });

            activeEl.target.classList.add('active')
        }

        document.querySelector("#one_month").addEventListener('click', function (e) {
            resetCssClasses(e);
            var lastDate = new Date(chartData.labels[chartData.labels.length - 1]);
            var oneMonthAgo = new Date(lastDate);
            oneMonthAgo.setMonth(lastDate.getMonth() - 1);
            chart.updateOptions({
                xaxis: {
                    min: oneMonthAgo.getTime(),
                    max: lastDate.getTime(),
                }
            });
        });

        document.querySelector("#six_months").addEventListener('click', function (e) {
            resetCssClasses(e);
            var lastDate = new Date(chartData.labels[chartData.labels.length - 1]);
            var sixMonthsAgo = new Date(lastDate);
            sixMonthsAgo.setMonth(lastDate.getMonth() - 6);
            chart.updateOptions({
                xaxis: {
                    min: sixMonthsAgo.getTime(),
                    max: lastDate.getTime(),
                }
            });
        });

        document.querySelector("#one_year").addEventListener('click', function (e) {
            resetCssClasses(e);
            var lastDate = new Date(chartData.labels[chartData.labels.length - 1]);
            var oneYearAgo = new Date(lastDate);
            oneYearAgo.setFullYear(lastDate.getFullYear() - 1);
            chart.updateOptions({
                xaxis: {
                    min: oneYearAgo.getTime(),
                    max: lastDate.getTime(),
                }
            });
        });

        document.querySelector("#all").addEventListener('click', function (e) {
            resetCssClasses(e)
            chart.updateOptions({
                xaxis: {
                    min: undefined,
                    max: undefined,
                }
            })
        })

    }

    fetchDataForChart();
});
