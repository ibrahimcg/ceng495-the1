// Main JavaScript file for the e-commerce app

document.addEventListener('DOMContentLoaded', function() {
    // Initialize any interactive elements
    
    // Example: Add fade-out for alert messages
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.classList.add('fade');
            setTimeout(() => {
                alert.remove();
            }, 500);
        }, 3000);
    });
    
    // Initialize any tooltips if using Bootstrap
    if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
        const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
        [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));
    }
});