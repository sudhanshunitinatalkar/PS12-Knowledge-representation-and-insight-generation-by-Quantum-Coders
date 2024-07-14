// DOM Elements
const fileUploadForm = document.getElementById('file-upload-form');
const successMessage = document.getElementById('success-message');
const errorMessage = document.getElementById('error-message');
const reportSection = document.getElementById('report-section');
const reportContent = document.getElementById('report-content');
const visualizationOptions = document.getElementById('visualization-options');
const visualizationForm = document.getElementById('visualization-form');
const visualizationFormSubmit = document.getElementById('vis-form');
const visualizationResult = document.getElementById('visualization-result');
const xAxisSelect = document.getElementById('x-axis');
const yAxisSelect = document.getElementById('y-axis');
const visButton = document.getElementById('generate-vis-btn');
const afterVisualizationDate = document.getElementById("after-text");

// File Upload Handler
fileUploadForm.addEventListener('submit', function (e) {
    e.preventDefault();

    const formData = new FormData(this);

    fetch('/api/upload', {
        method: 'POST',
        body: formData
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showSuccessMessage(data.message);
                fetchProcessedData();
            } else {
                showErrorMessage(data.error);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showErrorMessage('An error occurred during upload.');
        });
});

// Data Processing Functions
function fetchProcessedData() {
    fetch('/api/process_data')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                hideMessages();
                showBeforeReport(data.before_report);
                pollForCompletion();
            } else {
                showErrorMessage(data.error);
            }
        })
        .catch(error => {
            showErrorMessage('An error occurred while processing the data.');
        });
}

function pollForCompletion() {
    showSuccessMessage('Processing data... This may take a few minutes.');
    const pollInterval = setInterval(() => {
        fetch('/api/check_processing')
            .then(response => response.json())
            .then(data => {
                if (data.success && data.completed) {
                    clearInterval(pollInterval);
                    hideMessages();
                    showAfterReport(data.after_report, data.before_report );
                    showVisualizationOptions();
                }
            })
            .catch(error => {
                clearInterval(pollInterval);
                showErrorMessage('An error occurred while checking processing status.');
            });
    }, 2000);  // Check every 2 seconds
}

function showBeforeReport(reportData) {
    reportSection.style.display = 'block';
    // reportContent.innerHTML = '<h3>Data Report</h3>';
    // const beforeReport = document.createElement('div');
    const beforeReport = document.getElementById('before-text');
    beforeReport.className = 'before-report ';
    // beforeReport.innerHTML = '<h4>Before Processing</h4>';
    beforeReport.innerHTML = `<pre>${reportData}</pre>`;
    // reportContent.appendChild(beforeReport);

    setTimeout(() => {
        beforeReport.style.opacity = '1';
    }, 100);
}

function showAfterReport(afterReportData, beforeReportData) {
    console.log("after report data", afterReportData);
    const beforeReport = reportContent.querySelector('.before-report');
    // beforeReport.classList.remove('typing-animation');

    const afterReport = document.getElementById('after-text');
    afterReport.className = 'after-report';
    afterReport.innerHTML = `<pre>${afterReportData}</pre>`;
    // afterReport.style.opacity = '0';
    // reportContent.appendChild(afterReport);

    setTimeout(() => {
        // beforeReport.style.transform = 'translateX(-50%)';
        // afterReport.style.transform = 'translateX(-100%)';
        afterReport.style.opacity = '1';
    }, 100);
}

// Visualization Functions
function showVisualizationOptions() {
    visualizationOptions.style.display = 'block';
    fetchColumns();
}

function fetchColumns() {
    fetch('/api/get_columns')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                populateColumnDropdowns(data.columns);
            } else {
                showErrorMessage(data.error);
            }
        })
        .catch(error => {
            showErrorMessage('An error occurred while fetching columns.');
        });
}

function populateColumnDropdowns(columns) {
    xAxisSelect.innerHTML = '';
    yAxisSelect.innerHTML = '';

    columns.forEach(column => {
        xAxisSelect.appendChild(new Option(column, column));
        yAxisSelect.appendChild(new Option(column, column));
    });
}

visualizationFormSubmit.addEventListener('submit', function (e) {
    e.preventDefault();
    console.log('event', e);
    console.log('Form submitted');
    try {
        const formData = new FormData(visualizationFormSubmit);
        console.log('Form data:', formData.get('plot-type'), formData.get('x-axis'), formData.get('y-axis'));

        fetch('/api/visualize', {
            method: 'POST',
            body: formData
        })
            .then(response => response.json())
            .then(data => {
                console.log('API Response:', data);
                if (data.success) {
                    showSuccessMessage('Generating visualization...');
                    checkVisualization(formData.get('plot-type'), formData.get('x-axis'), formData.get('y-axis'));
                } else {
                    showErrorMessage(data.error);
                }
            })
            .catch(error => {
                console.error('Fetch Error:', error);
                showErrorMessage('An error occurred while generating the visualization.');
            });

    } catch (error) {
        console.log('error', error);
    }


});

function checkVisualization(plotType, xAxis, yAxis) {
    console.log('Checking visualization:', plotType, xAxis, yAxis);
    const checkInterval = setInterval(() => {
        fetch(`/api/check_visualization?plot_type=${plotType}&x_axis=${xAxis}&y_axis=${yAxis}`)
            .then(response => response.json())
            .then(data => {
                console.log('Check Response:', data);
                if (data.success) {
                    clearInterval(checkInterval);
                    displayVisualization(data.image_url);
                }
            })
            .catch(error => {
                console.error('Check Error:', error);
                clearInterval(checkInterval);
                showErrorMessage('An error occurred while checking for the visualization.');
            });
    }, 2000);  // Check every 2 seconds
}

function displayVisualization(imageUrl) {
    visualizationResult.innerHTML = `<img src="${imageUrl}" alt="Generated Visualization">`;
    visualizationResult.style.display = 'block';
}

// Utility Functions
function showSuccessMessage(message) {
    successMessage.textContent = message;
    successMessage.style.display = 'block';
    errorMessage.style.display = 'none';
}

function showErrorMessage(message) {
    errorMessage.textContent = message;
    errorMessage.style.display = 'block';
    successMessage.style.display = 'none';
}

function hideMessages() {
    successMessage.style.display = 'none';
    errorMessage.style.display = 'none';
}

// Event Listeners
document.getElementById('view-visualizations').addEventListener('click', function () {
    visualizationForm.style.display = 'block';
    visualizationFormSubmit.style.display = 'block';
});

// Print functionality
document.getElementById('print-visualizations').addEventListener('click', function () {
    window.print();
});

// Initialize the page
document.addEventListener('DOMContentLoaded', function () {
    // Fetch column names when the page loads
    fetch('/api/get_columns')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                populateColumnDropdowns(data.columns);
            } else {
                console.error('Failed to fetch columns:', data.error);
            }
        })
        .catch(error => console.error('Error:', error));
});