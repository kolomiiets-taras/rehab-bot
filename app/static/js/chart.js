Chart.defaults.global.defaultFontFamily = 'Nunito';
Chart.defaults.global.defaultFontColor = '#858796';

function number_format(number, decimals = 0, dec_point = '.', thousands_sep = ',') {
  number = (number + '').replace(',', '').replace(' ', '');
  const n = !isFinite(+number) ? 0 : +number;
  const prec = Math.abs(decimals);
  const sep = thousands_sep;
  const dec = dec_point;
  let s = '';

  const toFixedFix = (n, prec) => ('' + Math.round(n * Math.pow(10, prec)) / Math.pow(10, prec));

  s = (prec ? toFixedFix(n, prec) : '' + Math.round(n)).split('.');
  if (s[0].length > 3) {
    s[0] = s[0].replace(/\B(?=(?:\d{3})+(?!\d))/g, sep);
  }
  if ((s[1] || '').length < prec) {
    s[1] = s[1] || '';
    s[1] += new Array(prec - s[1].length + 1).join('0');
  }
  return s.join(dec);
}

export function renderChart(ctx, labels, before, after, beforeName, afterName, units) {
  new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [
        {
          label: beforeName,
          lineTension: 0.3,
          backgroundColor: "rgba(78, 115, 223, 0.05)",
          borderColor: "rgba(78, 115, 223, 1)",
          pointRadius: 3,
          pointBackgroundColor: "rgba(78, 115, 223, 1)",
          pointBorderColor: "rgba(78, 115, 223, 1)",
          pointHoverRadius: 3,
          pointHoverBackgroundColor: "rgba(78, 115, 223, 1)",
          pointHoverBorderColor: "rgba(78, 115, 223, 1)",
          pointHitRadius: 10,
          pointBorderWidth: 2,
          data: before
        },
        {
          label: afterName,
          lineTension: 0.3,
          backgroundColor: "rgba(231, 74, 59, 0.05)",
          borderColor: "rgba(231, 74, 59, 1)",
          pointRadius: 3,
          pointBackgroundColor: "rgba(231, 74, 59, 1)",
          pointBorderColor: "rgba(231, 74, 59, 1)",
          pointHoverRadius: 3,
          pointHoverBackgroundColor: "rgba(231, 74, 59, 1)",
          pointHoverBorderColor: "rgba(231, 74, 59, 1)",
          pointHitRadius: 10,
          pointBorderWidth: 2,
          data: after
        }
      ]
    },
    options: {
      maintainAspectRatio: false,
      layout: {
        padding: {
          left: 10,
          right: 25,
          top: 25,
          bottom: 0
        }
      },
      scales: {
        xAxes: [{
          time: { unit: 'date' },
          gridLines: { display: false, drawBorder: false },
          ticks: { maxTicksLimit: 7 }
        }],
        yAxes: [{
          ticks: {
            maxTicksLimit: 5,
            padding: 10,
            callback: value => number_format(value) + ' ' + units
          },
          gridLines: {
            color: "rgb(234, 236, 244)",
            zeroLineColor: "rgb(234, 236, 244)",
            drawBorder: false,
            borderDash: [2],
            zeroLineBorderDash: [2]
          }
        }]
      },
      legend: { display: true },
      tooltips: {
        backgroundColor: "rgb(255,255,255)",
        bodyFontColor: "#858796",
        titleMarginBottom: 10,
        titleFontColor: '#6e707e',
        titleFontSize: 14,
        borderColor: '#dddfeb',
        borderWidth: 1,
        xPadding: 15,
        yPadding: 15,
        displayColors: true,
        intersect: false,
        mode: 'index',
        caretPadding: 10,
        callbacks: {
          label: function(tooltipItem, chart) {
            const datasetLabel = chart.datasets[tooltipItem.datasetIndex].label || '';
            return datasetLabel + ': ' + number_format(tooltipItem.yLabel) + ' ' + units;
          }
        }
      }
    }
  });
}
