function loadStockTable() {
    fetch('/stock')
        .then(response => response.text())
        .then(data => {
            document.getElementById('stock-table-container').innerHTML = data;
            document.getElementById('stock-table-container').style.display = 'block';
        })
        .catch(error => console.error('Error fetching stock table:', error));
}

document.getElementById('update-stock-form').addEventListener('submit', function(event) {
    event.preventDefault();
    var formData = new FormData(this);
    fetch('/update_stock', {
        method: 'POST',
        body: formData
      })
      .then(response => {
        if (response.redirected) {
          window.location.href = response.url;
        }
      })
      .catch(error => console.error('Error updating stock:', error));
});
function updateDepartment(employeeId, newDepartment) {
    var formData = new FormData();
    formData.append('employee_id', employeeId);
    formData.append('new_department', newDepartment);
    fetch('/update_dep', {
        method: 'POST',
        body: formData
    })
    .then(response => {
        if (response.redirected) {
            window.location.href = response.url;
        }
    })
    .catch(error => console.error('Error updating department:', error));
}
function updateCard(employeeId, newCard) {
    var formData = new FormData();
    formData.append('employee_id', employeeId);
    formData.append('new_card', newCard);
    fetch('/update_card', {
        method: 'POST',
        body: formData
    })
    .then(response => {
        if (response.redirected) {
            window.location.href = response.url;
        }
    })
    .catch(error => console.error('Error assigning card:', error));
}
function loadEmployeesTable() {
    fetch('/employees')
        .then(response => response.text())
        .then(data => {
            document.getElementById('employee-table-container').innerHTML = data;
            document.getElementById('employee-table-container').style.display = 'block';
        })
        .catch(error => console.error('Error fetching employee table:', error));
}
function loadAccessTable() {
    fetch('/access_log')
        .then(response => response.text())
        .then(data => {
            document.getElementById('access-table-container').innerHTML = data;
            document.getElementById('access-table-container').style.display = 'block';
        })
        .catch(error => console.error('Error fetching access log data:', error));
}
function deleteLog(logId) {
    fetch('/delete_log', {
        method: 'POST',
        body: new URLSearchParams({
            'log_id': logId
        }),
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
    })
    .then(response => {
        if (response.ok) {
            loadAccessTable();
        } else {
            throw new Error('Failed to delete access log entry');
        }
    })
    .catch(error => console.error('Error deleting access log entry:', error));
}
function deleteSelected() {
    const selectedLogs = document.querySelectorAll('input[name="selectedLog"]:checked');
    const logIds = Array.from(selectedLogs).map(log => log.value);
    if (logIds.length > 0) {
        if (confirm("Are you sure you want to delete the selected entries?")) {
            logIds.forEach(logId => deleteLog(logId));
        }
    } else {
        alert("Please select at least one entry to delete.");
    }
}