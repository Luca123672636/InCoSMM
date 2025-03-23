/**
 * Initialize and manage all charts for the application
 */

// Setup color scheme
const chartColors = {
    present: 'rgba(75, 192, 192, 0.7)',
    absent: 'rgba(255, 99, 132, 0.7)',
    late: 'rgba(255, 159, 64, 0.7)',
    excused: 'rgba(153, 102, 255, 0.7)',
    borderPresent: 'rgb(75, 192, 192)',
    borderAbsent: 'rgb(255, 99, 132)',
    borderLate: 'rgb(255, 159, 64)',
    borderExcused: 'rgb(153, 102, 255)'
};

let attendanceBarChart = null;
let attendancePieChart = null;
let studentAttendanceChart = null;

/**
 * Initialize class attendance bar chart
 * @param {string} chartId - The ID of the canvas element
 * @param {Array} labels - The labels for the chart
 * @param {Array} presentData - The data for present students
 * @param {Array} absentData - The data for absent students
 * @param {Array} lateData - The data for late students
 */
function initClassAttendanceBarChart(chartId, labels, presentData, absentData, lateData) {
    const ctx = document.getElementById(chartId);
    
    // If chart already exists, destroy it
    if (attendanceBarChart) {
        attendanceBarChart.destroy();
    }
    
    attendanceBarChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Qatnashdi',
                    data: presentData,
                    backgroundColor: chartColors.present,
                    borderColor: chartColors.borderPresent,
                    borderWidth: 1
                },
                {
                    label: 'Qatnashmadi',
                    data: absentData,
                    backgroundColor: chartColors.absent,
                    borderColor: chartColors.borderAbsent,
                    borderWidth: 1
                },
                {
                    label: 'Kechikdi',
                    data: lateData,
                    backgroundColor: chartColors.late,
                    borderColor: chartColors.borderLate,
                    borderWidth: 1
                }
            ]
        },
        options: {
            responsive: true,
            scales: {
                x: {
                    stacked: false
                },
                y: {
                    beginAtZero: true,
                    max: 100,
                    ticks: {
                        callback: function(value) {
                            return value + '%';
                        }
                    }
                }
            },
            plugins: {
                title: {
                    display: true,
                    text: 'O\'quvchilar davomati'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return context.dataset.label + ': ' + context.raw + '%';
                        }
                    }
                }
            }
        }
    });
    
    return attendanceBarChart;
}

/**
 * Initialize attendance pie chart
 * @param {string} chartId - The ID of the canvas element
 * @param {number} present - The number of present attendances
 * @param {number} absent - The number of absent attendances
 * @param {number} late - The number of late attendances
 * @param {number} excused - The number of excused attendances
 */
function initAttendancePieChart(chartId, present, absent, late, excused) {
    const ctx = document.getElementById(chartId);
    
    // If chart already exists, destroy it
    if (attendancePieChart) {
        attendancePieChart.destroy();
    }
    
    attendancePieChart = new Chart(ctx, {
        type: 'pie',
        data: {
            labels: ['Qatnashdi', 'Qatnashmadi', 'Kechikdi', 'Sababli'],
            datasets: [{
                data: [present, absent, late, excused],
                backgroundColor: [
                    chartColors.present,
                    chartColors.absent,
                    chartColors.late,
                    chartColors.excused
                ],
                borderColor: [
                    chartColors.borderPresent,
                    chartColors.borderAbsent,
                    chartColors.borderLate,
                    chartColors.borderExcused
                ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: 'Davomat statistikasi'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.raw || 0;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = Math.round((value / total) * 100);
                            return `${label}: ${value} (${percentage}%)`;
                        }
                    }
                }
            }
        }
    });
    
    return attendancePieChart;
}

/**
 * Initialize student attendance chart across multiple classes
 * @param {string} chartId - The ID of the canvas element
 * @param {Array} labels - The class names
 * @param {Array} present - The count of present attendances per class
 * @param {Array} absent - The count of absent attendances per class
 * @param {Array} late - The count of late attendances per class
 * @param {Array} excused - The count of excused attendances per class
 */
function initStudentAttendanceChart(chartId, labels, present, absent, late, excused) {
    const ctx = document.getElementById(chartId);
    
    // If chart already exists, destroy it
    if (studentAttendanceChart) {
        studentAttendanceChart.destroy();
    }
    
    studentAttendanceChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Qatnashdi',
                    data: present,
                    backgroundColor: chartColors.present,
                    borderColor: chartColors.borderPresent,
                    borderWidth: 1
                },
                {
                    label: 'Qatnashmadi',
                    data: absent,
                    backgroundColor: chartColors.absent,
                    borderColor: chartColors.borderAbsent,
                    borderWidth: 1
                },
                {
                    label: 'Kechikdi',
                    data: late,
                    backgroundColor: chartColors.late,
                    borderColor: chartColors.borderLate,
                    borderWidth: 1
                },
                {
                    label: 'Sababli',
                    data: excused,
                    backgroundColor: chartColors.excused,
                    borderColor: chartColors.borderExcused,
                    borderWidth: 1
                }
            ]
        },
        options: {
            responsive: true,
            scales: {
                x: {
                    stacked: true
                },
                y: {
                    stacked: true,
                    beginAtZero: true
                }
            },
            plugins: {
                title: {
                    display: true,
                    text: 'Sinflardagi davomat'
                }
            }
        }
    });
    
    return studentAttendanceChart;
}

/**
 * Load class attendance data via AJAX
 * @param {number} classId - The ID of the class
 */
function loadClassAttendanceData(classId) {
    fetch(`/api/attendance_stats/${classId}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Ma\'lumotlarni yuklashda xatolik yuz berdi');
            }
            return response.json();
        })
        .then(data => {
            // Update bar chart
            const chartData = data.chart_data;
            initClassAttendanceBarChart(
                'attendanceBarChart', 
                chartData.labels,
                chartData.present_data,
                chartData.absent_data,
                chartData.late_data
            );
            
            // Update attendance table
            updateAttendanceTable(data.student_data);
        })
        .catch(error => {
            console.error('Error:', error);
            showAlert('Ma\'lumotlarni yuklashda xatolik: ' + error.message, 'danger');
        });
}

/**
 * Load student attendance data via AJAX
 * @param {number} studentId - The ID of the student
 */
function loadStudentAttendanceData(studentId) {
    fetch(`/api/student_attendance/${studentId}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Ma\'lumotlarni yuklashda xatolik yuz berdi');
            }
            return response.json();
        })
        .then(data => {
            // Update student attendance chart
            const chartData = data.chart_data;
            initStudentAttendanceChart(
                'studentAttendanceChart',
                chartData.labels,
                chartData.present,
                chartData.absent,
                chartData.late,
                chartData.excused
            );
            
            // Update class data table if available
            if (document.getElementById('classDataTable')) {
                updateClassDataTable(data.class_data);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showAlert('Ma\'lumotlarni yuklashda xatolik: ' + error.message, 'danger');
        });
}

/**
 * Update the attendance table with new data
 * @param {Array} studentData - The updated student data
 */
function updateAttendanceTable(studentData) {
    const tableBody = document.getElementById('attendanceTableBody');
    if (!tableBody) return;
    
    tableBody.innerHTML = '';
    
    studentData.forEach(student => {
        const row = document.createElement('tr');
        
        // Create student name cell
        const nameCell = document.createElement('td');
        nameCell.textContent = student.name;
        row.appendChild(nameCell);
        
        // Create present count cell
        const presentCell = document.createElement('td');
        presentCell.textContent = student.present;
        row.appendChild(presentCell);
        
        // Create absent count cell
        const absentCell = document.createElement('td');
        absentCell.textContent = student.absent;
        row.appendChild(absentCell);
        
        // Create late count cell
        const lateCell = document.createElement('td');
        lateCell.textContent = student.late;
        row.appendChild(lateCell);
        
        // Create excused count cell
        const excusedCell = document.createElement('td');
        excusedCell.textContent = student.excused;
        row.appendChild(excusedCell);
        
        // Create percentage cell
        const percentCell = document.createElement('td');
        const badge = document.createElement('span');
        badge.classList.add('badge');
        
        if (student.present_percent >= 90) {
            badge.classList.add('bg-success');
        } else if (student.present_percent >= 75) {
            badge.classList.add('bg-info');
        } else if (student.present_percent >= 50) {
            badge.classList.add('bg-warning');
        } else {
            badge.classList.add('bg-danger');
        }
        
        badge.textContent = `${student.present_percent}%`;
        percentCell.appendChild(badge);
        row.appendChild(percentCell);
        
        tableBody.appendChild(row);
    });
}

/**
 * Update the class data table
 * @param {Array} classData - The updated class data
 */
function updateClassDataTable(classData) {
    const tableBody = document.getElementById('classDataTableBody');
    if (!tableBody) return;
    
    tableBody.innerHTML = '';
    
    classData.forEach(data => {
        const row = document.createElement('tr');
        
        // Create class name cell
        const nameCell = document.createElement('td');
        nameCell.textContent = data.class_name;
        row.appendChild(nameCell);
        
        // Create present count cell
        const presentCell = document.createElement('td');
        presentCell.textContent = data.present;
        row.appendChild(presentCell);
        
        // Create absent count cell
        const absentCell = document.createElement('td');
        absentCell.textContent = data.absent;
        row.appendChild(absentCell);
        
        // Create late count cell
        const lateCell = document.createElement('td');
        lateCell.textContent = data.late;
        row.appendChild(lateCell);
        
        // Create excused count cell
        const excusedCell = document.createElement('td');
        excusedCell.textContent = data.excused;
        row.appendChild(excusedCell);
        
        // Create total cell
        const totalCell = document.createElement('td');
        totalCell.textContent = data.total;
        row.appendChild(totalCell);
        
        // Create percentage cell
        const percentCell = document.createElement('td');
        if (data.total > 0) {
            const percentage = Math.round((data.present / data.total) * 100);
            
            const badge = document.createElement('span');
            badge.classList.add('badge');
            
            if (percentage >= 90) {
                badge.classList.add('bg-success');
            } else if (percentage >= 75) {
                badge.classList.add('bg-info');
            } else if (percentage >= 50) {
                badge.classList.add('bg-warning');
            } else {
                badge.classList.add('bg-danger');
            }
            
            badge.textContent = `${percentage}%`;
            percentCell.appendChild(badge);
        } else {
            percentCell.textContent = 'N/A';
        }
        row.appendChild(percentCell);
        
        tableBody.appendChild(row);
    });
}

/**
 * Show an alert message
 * @param {string} message - The message to display
 * @param {string} type - The type of alert (success, danger, warning, info)
 */
function showAlert(message, type = 'info') {
    const alertsContainer = document.getElementById('alerts-container');
    if (!alertsContainer) return;
    
    const alert = document.createElement('div');
    alert.classList.add('alert', `alert-${type}`, 'alert-dismissible', 'fade', 'show');
    alert.setAttribute('role', 'alert');
    
    alert.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    alertsContainer.appendChild(alert);
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        alert.classList.remove('show');
        setTimeout(() => {
            alert.remove();
        }, 150);
    }, 5000);
}
