// static/js/charts.js

// 1st Plot: Inventory vs. Total Sold (All Time)
function initInventorySalesChart(data) {
    // Ensure no null values in sell-through array
    data.sell_through = data.sell_through.map(v => v ?? 0);

    const ctx = document.getElementById('inventorySalesChart');

    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.labels.map(name => name.length > 12 ? name.slice(0, 12) + '...' : name),
            datasets: [
                {
                    label: 'Inventory',
                    data: data.inventory,
                    backgroundColor: 'rgba(54, 162, 235, 0.7)',
                    yAxisID: 'y'
                },
                {
                    label: 'Total Sold',
                    data: data.sold,
                    backgroundColor: 'rgba(255, 99, 132, 0.7)',
                    yAxisID: 'y'
                },
                {
                    label: 'Sell-Through Rate',
                    type: 'line',
                    data: data.sell_through,
                    borderColor: 'rgba(255, 159, 64, 0.9)',
                    backgroundColor: 'rgba(255, 159, 64, 0.3)',
                    yAxisID: 'y1',
                    tension: 0.3,
                    fill: false,
                    pointRadius: 4,
                    spanGaps: true // Allow connecting points even if some are missing
                }
            ]
        },
        options: {
            responsive: true,
            interaction: {
                mode: 'index',
                intersect: false
            },
            plugins: {
                legend: {
                    position: 'top',
                    labels: {
                        boxWidth: 12,
                        font: {
                            size: 12
                        }
                    }
                }
            },
            scales: {
                x: {
                    ticks: {
                        maxRotation: 45,
                        minRotation: 30
                    },
                    grid: { display: false },
                    title: {
                        display: true,
                        text: 'Product',
                        font: { weight: 'bold' }
                    }
                },
                y: {
                    beginAtZero: true,
                    max: 100,  // Cap inventory axis at 100 for better visualization
                    title: {
                        display: true,
                        text: 'Inventory',
                        font: { weight: 'bold' }
                    },
                    ticks: {
                        callback: function (value) {
                            return value === 100 ? '100+' : value;
                        }
                    },
                    grid: {
                        display: false
                    }
                },

                y1: {
                    type: 'linear',
                    position: 'right',
                    min: 0,
                    max: 1.0,
                    ticks: {
                        callback: value => `${Math.round(value * 100)}%`
                    },
                    title: {
                        display: true,
                        text: 'Sell-Through Rate',
                        font: { weight: 'bold' }
                    },
                    grid: { drawOnChartArea: false }
                }
            }
        }
    });
}

// 2nd Plot: Top Products by Order Count (All Time)
function initProductPopularityChart(data) {
    const ctx = document.getElementById('productPopularityChart');

    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.labels.map(name => name.length > 12 ? name.slice(0, 12) + '...' : name),
            datasets: [{
                label: 'Order Count',
                data: data.data,
                backgroundColor: 'rgba(75, 192, 192, 0.7)',
                borderRadius: 5,           // Rounded corners
                maxBarThickness: 40        // Limit maximum bar width
            }]
        },
        options: {
            responsive: true,
            interaction: {
                mode: 'index',
                intersect: false
            },
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    mode: 'index',
                    intersect: false
                }
            },
            scales: {
                x: {
                    ticks: {
                        maxRotation: 45,
                        minRotation: 30
                    },
                    grid: { display: false },
                    title: {
                        display: true,
                        text: 'Product',
                        font: { weight: 'bold' }
                    }
                },
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Order Count',
                        font: { weight: 'bold' }
                    },
                    ticks: {
                        stepSize: 1
                    },
                    grid: { display: false }
                }
            }
        }
    });
}


// 3rd Plot: Order Status Distribution (All Time)
function initOrderStatusChart(data) {
    const ctx = document.getElementById('orderStatusChart');

    // Define color mapping for different order statuses
    const statusColorMap = {
        'Cancelled': 'rgba(255, 99, 132, 0.7)',     // red
        'Fulfilled': 'rgba(75, 192, 75, 0.7)',     // green
        'Pending': 'rgba(255, 206, 86, 0.7)',      // yellow
        'Shipped': 'rgba(54, 162, 235, 0.7)',       // blue
        'Processing': 'rgba(153, 102, 255, 0.7)',   //purple
        'Delivered': 'rgba(255, 159, 64, 0.7)'      //orange
    };

    // Capitalize labels and map colors accordingly
    const labels = data.labels.map(status =>
        status.charAt(0).toUpperCase() + status.slice(1).toLowerCase()
    );
    const colors = labels.map(label => statusColorMap[label] || 'rgba(200, 200, 200, 0.7)');

    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Order Count',
                data: data.counts,
                backgroundColor: colors,
                borderRadius: 5
            }]
        },
        options: {
            indexAxis: 'y', // Horizontal bar chart
            responsive: true,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: function (context) {
                            const total = data.counts.reduce((a, b) => a + b, 0);
                            const percent = ((context.raw / total) * 100).toFixed(1);
                            return `${context.raw} orders (${percent}%)`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Order Count',
                        font: { weight: 'bold' }
                    },
                    grid: { display: false }
                },
                y: {
                    title: {
                        display: true,
                        text: 'Status',
                        font: { weight: 'bold' }
                    },
                    grid: { display: false }
                }
            }
        }
    });
}