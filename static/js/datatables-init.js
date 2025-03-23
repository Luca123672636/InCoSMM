/**
 * Initialize DataTables for tables in the application
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize all tables with the class 'datatable'
    const tables = document.querySelectorAll('.datatable');
    
    tables.forEach(table => {
        initDataTable(table);
    });
});

/**
 * Initialize a DataTable
 * @param {HTMLElement} tableElement - The table element
 */
function initDataTable(tableElement) {
    // Set custom language for Uzbek
    const uzLanguage = {
        "processing": "Ma'lumotlar yuklanmoqda...",
        "search": "Qidirish:",
        "lengthMenu": "_MENU_ ta yozuvni ko'rsatish",
        "info": "_TOTAL_ ta yozuvdan _START_ dan _END_ gacha ko'rsatilmoqda",
        "infoEmpty": "Yozuvlar mavjud emas",
        "infoFiltered": "(_MAX_ ta yozuvdan filtrlangan)",
        "loadingRecords": "Yuklanmoqda...",
        "zeroRecords": "Mos yozuvlar topilmadi",
        "emptyTable": "Jadvalda ma'lumotlar mavjud emas",
        "paginate": {
            "first": "Birinchi",
            "previous": "Avvalgi",
            "next": "Keyingi",
            "last": "Oxirgi"
        },
        "aria": {
            "sortAscending": ": ustunni o'sish tartibida saralash",
            "sortDescending": ": ustunni kamayish tartibida saralash"
        }
    };
    
    // Initialize DataTable with options
    const table = $(tableElement).DataTable({
        language: uzLanguage,
        responsive: true,
        dom: 'Bfrtip',
        buttons: [
            'copy', 'excel', 'pdf', 'print'
        ],
        order: [[0, 'asc']]
    });
    
    // Add custom search functionality if needed
    const tableId = tableElement.id;
    const customSearchInput = document.getElementById(`${tableId}_search`);
    
    if (customSearchInput) {
        customSearchInput.addEventListener('keyup', function() {
            table.search(this.value).draw();
        });
    }
}

/**
 * Reinitialize a DataTable after content changes
 * @param {string} tableId - The ID of the table
 */
function refreshDataTable(tableId) {
    const table = $(`#${tableId}`).DataTable();
    table.destroy();
    
    initDataTable(document.getElementById(tableId));
}

/**
 * Export table data to Excel
 * @param {string} tableId - The ID of the table
 * @param {string} fileName - The name of the exported file
 */
function exportTableToExcel(tableId, fileName) {
    const table = $(`#${tableId}`).DataTable();
    
    // Use DataTables built-in export
    table.button('.buttons-excel').trigger();
}

/**
 * Export table data to PDF
 * @param {string} tableId - The ID of the table
 * @param {string} fileName - The name of the exported file
 */
function exportTableToPdf(tableId, fileName) {
    const table = $(`#${tableId}`).DataTable();
    
    // Use DataTables built-in export
    table.button('.buttons-pdf').trigger();
}

/**
 * Print table
 * @param {string} tableId - The ID of the table
 */
function printTable(tableId) {
    const table = $(`#${tableId}`).DataTable();
    
    // Use DataTables built-in print
    table.button('.buttons-print').trigger();
}
