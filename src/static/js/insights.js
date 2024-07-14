// DOM Elements
const fileUploadForm = document.getElementById('file-upload-form');
const successMessage = document.getElementById('success-message');
const errorMessage = document.getElementById('error-message');
const reportSection = document.getElementById('report-section');
const reportContent = document.getElementById('report-content');
const afterVisualizationDate = document.getElementById("after-text");
const generateReportBtn = document.getElementById('generate-report-btn');
const generatedReportSection = document.getElementById('generated-report-section');
const generatedReportContent = document.getElementById('generated-report-content');
const printReportBtn = document.getElementById('print-report-btn');
const chatbox = document.getElementById('chatbox');
const queryForm = document.getElementById('query-form');
const queryInput = document.getElementById('query-input');

// File Upload Handler
fileUploadForm.addEventListener('submit', function (e) {
    e.preventDefault();

    const formData = new FormData(this);

    fetch('/api/upload_insight', {
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
    fetch('/api/process_data_insight')
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
        fetch('/api/check_processing_insight')
        .then(response => response.json())
        .then(data => {
            if (data.success && data.completed) {
                clearInterval(pollInterval);
                hideMessages();
                showAfterReport(data.after_report);
                checkReportGeneration();
            }
        })
        .catch(error => {
            clearInterval(pollInterval);
            showErrorMessage('An error occurred while checking processing status.');
        });
    }, 2000);  // Check every 2 seconds
}

function checkReportGeneration() {
    const checkInterval = setInterval(() => {
        fetch('/api/check_report_insight')
        .then(response => response.json())
        .then(data => {
            if (data.success && data.completed) {
                clearInterval(checkInterval);
                showGenerateReportButton();
                showChatbox();
            }
        })
        .catch(error => {
            clearInterval(checkInterval);
            showErrorMessage('An error occurred while checking report generation status.');
        });
    }, 2000);  // Check every 2 seconds
}

function showBeforeReport(reportData) {
    reportSection.style.display = 'block';
    const beforeReport = document.getElementById('before-text');
    beforeReport.className = 'before-report';
    beforeReport.innerHTML = `<pre>${reportData}</pre>`;
    setTimeout(() => {
        beforeReport.style.opacity = '1';
    }, 100);
}

function showAfterReport(afterReportData) {
    const afterReport = document.getElementById('after-text');
    afterReport.className = 'after-report';
    afterReport.innerHTML = `<pre>${afterReportData}</pre>`;
    setTimeout(() => {
        afterReport.style.opacity = '1';
        // Show loader after after-text is displayed
        document.getElementById('loader').style.display = 'block';
    }, 100);
}

function showGenerateReportButton() {
    // Hide loader when generate report button is shown
    document.getElementById('loader').style.display = 'none';
    generateReportBtn.style.display = 'block';
}

function showChatbox() {
    const chatboxSection = document.getElementById('chatbox-section');
    chatboxSection.style.display = 'block';
}

// Generate Report Functions
generateReportBtn.addEventListener('click', generateReport);
printReportBtn.addEventListener('click', printReport);

function generateReport() {
    document.getElementById('loader').style.display = 'none';
    fetch('/api/generate_report')
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            reportSection.style.display = 'none';
            generatedReportSection.style.display = 'block';
            generatedReportContent.innerHTML = `<pre>${data.report}</pre>`;
            
            // Display images
            const imagesContainer = document.getElementById('report-images');
            imagesContainer.innerHTML = '';
            data.images.forEach(imageSrc => {
                const img = document.createElement('img');
                img.src = imageSrc;
                img.style.maxWidth = '100%';
                img.style.marginBottom = '20px';
                imagesContainer.appendChild(img);
            });

            generateReportBtn.style.display = 'none';
        } else {
            showErrorMessage(data.error);
        }
    })
    .catch(error => {
        showErrorMessage('An error occurred while generating the report.');
    });
}

function printReport() {
    const reportContent = generatedReportSection.innerHTML;
    const printWindow = window.open('', '', 'height=600,width=800');
    printWindow.document.write('<html><head><title>Report</title>');
    printWindow.document.write('<style>body { font-family: Arial, sans-serif; }</style>');
    printWindow.document.write('</head><body>');
    printWindow.document.write(reportContent);
    printWindow.document.write('</body></html>');
    printWindow.document.close();
    printWindow.print();
}

// Chatbox functionality
function sendMessage() {
    const message = queryInput.value.trim();
    if (message) {
        appendMessage('You', message);
        sendQuery(message);
        queryInput.value = '';
    }
}

function appendMessage(sender, message) {
    const messageElement = document.createElement('p');
    messageElement.innerHTML = `<strong>${sender}:</strong> ${message}`;
    chatbox.appendChild(messageElement);
    chatbox.scrollTop = chatbox.scrollHeight;
}

function sendQuery(query) {
    fetch('/api/chat_query', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ query: query })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            appendMessage('AI', data.response);
        } else {
            appendMessage('AI', 'Error: ' + data.error);
        }
    })
    .catch(error => {
        appendMessage('AI', 'Error: ' + error.message);
    });
}

queryForm.addEventListener('submit', function(event) {
    event.preventDefault();
    sendMessage();
});

queryInput.addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        e.preventDefault();
        sendMessage();
    }
});

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