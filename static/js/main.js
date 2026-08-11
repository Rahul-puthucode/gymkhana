/**
 * GYMKHANA Main Client JavaScript Utility Module
 */

document.addEventListener('DOMContentLoaded', function () {
    // Sidebar Toggle for Mobile View
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebar = document.getElementById('appSidebar');

    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener('click', function () {
            sidebar.classList.toggle('show');
        });
    }

    // Auto-dismiss Alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(function (alert) {
        setTimeout(function () {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });

    // Check Notifications Unread Count via API if logged in
    const notifBadge = document.getElementById('navNotifBadge');
    if (notifBadge) {
        fetchUnreadNotificationCount();
        setInterval(fetchUnreadNotificationCount, 30000); // refresh every 30s
    }
});

function fetchUnreadNotificationCount() {
    fetch('/notifications/api/unread-count')
        .then(response => response.json())
        .then(data => {
            const badge = document.getElementById('navNotifBadge');
            if (badge && data.count !== undefined) {
                if (data.count > 0) {
                    badge.textContent = data.count;
                    badge.style.display = 'inline-block';
                } else {
                    badge.style.display = 'none';
                }
            }
        })
        .catch(err => console.log('Notification fetch skipped:', err));
}

function confirmAction(message) {
    return confirm(message || 'Are you sure you want to perform this action?');
}
