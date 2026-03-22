function toggleValidator(el) {
    const body = el.nextElementSibling;
    if (!body || !body.classList.contains("validator-body")) return;
    body.classList.toggle("open");
    el.querySelector(".chevron").classList.toggle("open");
}

const chartColors = {
    green: "#10b981",
    red: "#ef4444",
    orange: "#f59e0b",
    blue: "#3b82f6",
    purple: "#8b5cf6",
    cyan: "#06b6d4",
    pink: "#ec4899",
};

const colorList = [
    chartColors.blue,
    chartColors.orange,
    chartColors.purple,
    chartColors.cyan,
    chartColors.pink,
    chartColors.red,
    chartColors.green,
];

Chart.defaults.color = "#94a3b8";
Chart.defaults.borderColor = "rgba(51,65,85,0.5)";

const passCount = {{ pass_count }};
const failCount = {{ fail_count }};
const validatorNames = {{ validator_names_json | safe }};
const errorCounts = {{ error_counts_json | safe }};
const history = {{ history_json | safe }};

new Chart(document.getElementById("passfailChart"), {
    type: "doughnut",
    data: {
        labels: ["Passed", "Failed"],
        datasets: [
            {
                data: [passCount, failCount],
                backgroundColor: [chartColors.green, chartColors.red],
                borderWidth: 0,
            },
        ],
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: "65%",
        plugins: {
            legend: {
                position: "bottom",
                labels: { padding: 16, usePointStyle: true, pointStyle: "circle" },
            },
        },
    },
});

const barColors = validatorNames.map((_, index) =>
    errorCounts[index] === 0 ? chartColors.green : colorList[index % colorList.length]
);

new Chart(document.getElementById("errorsChart"), {
    type: "bar",
    data: {
        labels: validatorNames,
        datasets: [
            {
                label: "Errors",
                data: errorCounts,
                backgroundColor: barColors,
                borderRadius: 4,
                borderSkipped: false,
            },
        ],
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        indexAxis: "y",
        plugins: { legend: { display: false } },
        scales: {
            x: { grid: { color: "rgba(51,65,85,0.3)" }, ticks: { precision: 0 } },
            y: { grid: { display: false } },
        },
    },
});

const historyContainer = document.getElementById("historyContainer");

if (history.length > 1) {
    const labels = history.map((entry) => entry.date);
    const totals = history.map((entry) => entry.total_errors);
    const statuses = history.map((entry) => entry.overall_passed);

    new Chart(document.getElementById("historyChart"), {
        type: "line",
        data: {
            labels,
            datasets: [
                {
                    label: "Total Errors",
                    data: totals,
                    borderColor: chartColors.orange,
                    backgroundColor: "rgba(245,158,11,0.1)",
                    fill: true,
                    tension: 0.3,
                    pointRadius: 4,
                    pointBackgroundColor: statuses.map((passed) =>
                        passed ? chartColors.green : chartColors.red
                    ),
                    pointBorderColor: statuses.map((passed) =>
                        passed ? chartColors.green : chartColors.red
                    ),
                },
            ],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        afterLabel(ctx) {
                            return statuses[ctx.dataIndex] ? "Status: PASSED" : "Status: FAILED";
                        },
                    },
                },
            },
            scales: {
                x: { grid: { color: "rgba(51,65,85,0.3)" } },
                y: {
                    grid: { color: "rgba(51,65,85,0.3)" },
                    beginAtZero: true,
                    ticks: { precision: 0 },
                },
            },
        },
    });
} else {
    document.getElementById("historyChart").style.display = "none";
    historyContainer.innerHTML =
        '<p class="no-history">Run validations multiple times with --report to see trends over time.</p>';
}
