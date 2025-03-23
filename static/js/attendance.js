/**
 * JavaScript functions for attendance management
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize attendance form events
    initAttendanceForm();
    
    // Initialize attendance filters
    initAttendanceFilters();
});

/**
 * Initialize attendance form events
 */
function initAttendanceForm() {
    // Handle status change - highlight selected status
    const statusSelects = document.querySelectorAll('.attendance-status');
    if (statusSelects) {
        statusSelects.forEach(select => {
            // Set initial color on load
            updateStatusColor(select);
            
            // Update color on change
            select.addEventListener('change', function() {
                updateStatusColor(this);
            });
        });
    }
    
    // Select all buttons functionality
    const selectAllButtons = {
        present: document.getElementById('selectAllPresent'),
        absent: document.getElementById('selectAllAbsent'),
        late: document.getElementById('selectAllLate'),
        excused: document.getElementById('selectAllExcused')
    };
    
    Object.entries(selectAllButtons).forEach(([status, button]) => {
        if (button) {
            button.addEventListener('click', function(e) {
                e.preventDefault();
                setAllStatuses(status);
            });
        }
    });
}

/**
 * Update the visual appearance of the status select based on selected value
 * @param {HTMLElement} select - The select element
 */
function updateStatusColor(select) {
    // Remove all status classes
    select.classList.remove('status-present', 'status-absent', 'status-late', 'status-excused');
    
    // Add appropriate class based on selected value
    const status = select.value;
    select.classList.add(`status-${status}`);
    
    // Update parent row if needed
    const row = select.closest('tr');
    if (row) {
        row.classList.remove('table-success', 'table-danger', 'table-warning', 'table-info');
        
        switch (status) {
            case 'present':
                row.classList.add('table-success');
                break;
            case 'absent':
                row.classList.add('table-danger');
                break;
            case 'late':
                row.classList.add('table-warning');
                break;
            case 'excused':
                row.classList.add('table-info');
                break;
        }
    }
}

/**
 * Set all attendance statuses to the same value
 * @param {string} status - The status value to set (present, absent, late, excused)
 */
function setAllStatuses(status) {
    const statusSelects = document.querySelectorAll('.attendance-status');
    
    statusSelects.forEach(select => {
        select.value = status;
        updateStatusColor(select);
    });
}

/**
 * Initialize attendance filters and search functionality
 */
function initAttendanceFilters() {
    const searchInput = document.getElementById('searchStudent');
    const statusFilter = document.getElementById('filterStatus');
    
    if (searchInput) {
        searchInput.addEventListener('input', filterStudents);
    }
    
    if (statusFilter) {
        statusFilter.addEventListener('change', filterStudents);
    }
}

/**
 * Filter students in the attendance table
 */
function filterStudents() {
    const searchInput = document.getElementById('searchStudent');
    const statusFilter = document.getElementById('filterStatus');
    
    if (!searchInput && !statusFilter) return;
    
    const searchTerm = searchInput ? searchInput.value.toLowerCase() : '';
    const statusTerm = statusFilter ? statusFilter.value : '';
    
    const rows = document.querySelectorAll('#attendanceTable tbody tr');
    
    rows.forEach(row => {
        const studentName = row.querySelector('td:first-child').textContent.toLowerCase();
        const statusSelect = row.querySelector('.attendance-status');
        const statusValue = statusSelect ? statusSelect.value : '';
        
        const nameMatch = searchTerm === '' || studentName.includes(searchTerm);
        const statusMatch = statusTerm === '' || statusValue === statusTerm;
        
        if (nameMatch && statusMatch) {
            row.style.display = '';
        } else {
            row.style.display = 'none';
        }
    });
}

/**
 * Toggle notes field visibility
 * @param {number} studentId - The ID of the student
 */
function toggleNotes(studentId) {
    const notesRow = document.getElementById(`notesRow_${studentId}`);
    
    if (notesRow) {
        if (notesRow.style.display === 'none' || notesRow.style.display === '') {
            notesRow.style.display = 'table-row';
        } else {
            notesRow.style.display = 'none';
        }
    }
}

/**
 * Format a date for display
 * @param {string} dateString - The date string to format
 * @returns {string} The formatted date
 */
function formatDate(dateString) {
    const options = { year: 'numeric', month: 'long', day: 'numeric' };
    const date = new Date(dateString);
    return date.toLocaleDateString('uz-UZ', options);
}

/**
 * Format a time for display
 * @param {string} timeString - The time string to format
 * @returns {string} The formatted time
 */
function formatTime(timeString) {
    const options = { hour: '2-digit', minute: '2-digit' };
    const time = new Date(`2000-01-01T${timeString}`);
    return time.toLocaleTimeString('uz-UZ', options);
}
