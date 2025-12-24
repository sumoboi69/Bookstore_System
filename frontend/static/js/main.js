/**
 * Main JavaScript file for Bookstore System
 */

// Add to cart functionality
document.addEventListener('DOMContentLoaded', function() {
    // Handle add to cart buttons
    const addToCartButtons = document.querySelectorAll('.add-to-cart');

    addToCartButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            const bookId = this.getAttribute('data-id');
            // Form will handle the submission
        });
    });

    // Cart quantity update buttons
    const quantityButtons = document.querySelectorAll('.btn-group button');
    quantityButtons.forEach(button => {
        button.addEventListener('click', function() {
            // Handle quantity updates if needed
        });
    });

    // Form validation
    const forms = document.querySelectorAll('.needs-validation');
    forms.forEach(form => {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });
});

// Auto-dismiss alerts after 5 seconds
setTimeout(function() {
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        const bsAlert = new bootstrap.Alert(alert);
        bsAlert.close();
    });
}, 5000);

