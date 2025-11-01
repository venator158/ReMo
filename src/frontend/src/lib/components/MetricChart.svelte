<script>
  import { Chart, registerables } from 'chart.js';
  import { onMount, onDestroy } from 'svelte';

  Chart.register(...registerables);

  export let data = [];
  export let label = 'Metric';
  export let color = '#4f46e5';
  export let yAxisLabel = 'Value';
  export let maxDataPoints = 60;

  let canvas;
  let chart;

  onMount(() => {
    const ctx = canvas.getContext('2d');
    
    chart = new Chart(ctx, {
      type: 'line',
      data: {
        labels: [],
        datasets: [{
          label: label,
          data: [],
          borderColor: color,
          backgroundColor: color + '20',
          borderWidth: 2,
          tension: 0.4,
          fill: true,
          pointRadius: 0,
          pointHoverRadius: 4,
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: {
          intersect: false,
          mode: 'index',
        },
        plugins: {
          legend: {
            display: true,
            labels: {
              color: '#f1f5f9',
              font: {
                size: 12
              }
            }
          },
          tooltip: {
            backgroundColor: '#1e293b',
            titleColor: '#f1f5f9',
            bodyColor: '#f1f5f9',
            borderColor: '#334155',
            borderWidth: 1,
            padding: 10,
            displayColors: false,
          }
        },
        scales: {
          x: {
            display: true,
            grid: {
              color: '#334155',
              drawBorder: false,
            },
            ticks: {
              color: '#94a3b8',
              maxTicksLimit: 10,
              font: {
                size: 10
              }
            }
          },
          y: {
            display: true,
            title: {
              display: true,
              text: yAxisLabel,
              color: '#94a3b8',
              font: {
                size: 12
              }
            },
            grid: {
              color: '#334155',
              drawBorder: false,
            },
            ticks: {
              color: '#94a3b8',
              font: {
                size: 10
              }
            }
          }
        }
      }
    });

    updateChart();
  });

  onDestroy(() => {
    if (chart) {
      chart.destroy();
    }
  });

  function updateChart() {
    if (!chart || !data) return;

    const labels = data.map(item => {
      const date = new Date(item.timestamp);
      return date.toLocaleTimeString('en-US', { 
        hour: '2-digit', 
        minute: '2-digit',
        second: '2-digit'
      });
    });

    const values = data.map(item => item.value);

    // Limit data points to prevent overcrowding
    const limitedLabels = labels.slice(-maxDataPoints);
    const limitedValues = values.slice(-maxDataPoints);

    chart.data.labels = limitedLabels;
    chart.data.datasets[0].data = limitedValues;
    chart.update('none'); // Update without animation for smoother real-time updates
  }

  $: if (chart && data) {
    updateChart();
  }
</script>

<div class="chart-container">
  <canvas bind:this={canvas}></canvas>
</div>

<style>
  .chart-container {
    position: relative;
    height: 300px;
    width: 100%;
  }
</style>
