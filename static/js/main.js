$(document).ready(function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl)
    });

    // Format dates in tables
    function formatDate(dateStr) {
        if (!dateStr) return '';
        const date = new Date(dateStr);
        return date.toLocaleDateString('en-IN', {
            day: '2-digit',
            month: 'short',
            year: 'numeric'
        });
    }

    // Format all date cells
    $('.table td:contains("/")').each(function() {
        const dateStr = $(this).text().trim();
        if (dateStr.match(/^\d{2}\/\d{2}\/\d{4}$/)) {
            $(this).text(formatDate(dateStr));
        }
    });

    // Add copy functionality for CNR numbers
    $('.copy-cnr').click(function(e) {
        e.preventDefault();
        const cnr = $(this).data('cnr');
        navigator.clipboard.writeText(cnr).then(function() {
            const tooltip = bootstrap.Tooltip.getInstance(e.target);
            const originalTitle = $(e.target).attr('data-bs-original-title');
            
            $(e.target).attr('data-bs-original-title', 'Copied!');
            tooltip.show();
            
            setTimeout(function() {
                $(e.target).attr('data-bs-original-title', originalTitle);
                tooltip.hide();
            }, 1000);
        });
    });

    // Add table sorting functionality
    $('.sortable').click(function() {
        const table = $(this).closest('table');
        const rows = table.find('tr:gt(0)').toArray();
        const column = $(this).index();
        const ascending = $(this).hasClass('asc');
        
        rows.sort(function(a, b) {
            const A = $(a).children('td').eq(column).text().trim();
            const B = $(b).children('td').eq(column).text().trim();
            
            if (A < B) return ascending ? 1 : -1;
            if (A > B) return ascending ? -1 : 1;
            return 0;
        });
        
        $(this).toggleClass('asc');
        $.each(rows, function(index, row) {
            table.children('tbody').append(row);
        });
    });

    // Add search functionality for case tables
    $('#caseSearch').on('keyup', function() {
        const value = $(this).val().toLowerCase();
        $('#casesTable tbody tr').filter(function() {
            $(this).toggle($(this).text().toLowerCase().indexOf(value) > -1);
        });
    });

    // Smooth scroll to sections
    $('a[href^="#"]').on('click', function(e) {
        e.preventDefault();
        const target = $(this.hash);
        if (target.length) {
            $('html, body').animate({
                scrollTop: target.offset().top - 70
            }, 500);
        }
    });

    // Add loading state to buttons
    $('.btn').click(function() {
        const $btn = $(this);
        if ($btn.attr('type') === 'submit' && !$btn.hasClass('no-loading')) {
            const originalText = $btn.html();
            $btn.prop('disabled', true)
                .html('<span class="spinner-border spinner-border-sm me-2"></span>Loading...');
            
            setTimeout(function() {
                $btn.prop('disabled', false).html(originalText);
            }, 20000); // Timeout after 20 seconds
        }
    });

    // Handle form validation
    $('form').on('submit', function() {
        const form = $(this)[0];
        if (!form.checkValidity()) {
            event.preventDefault();
            event.stopPropagation();
        }
        $(this).addClass('was-validated');
    });

    // Add responsive table wrappers
    $('.table').each(function() {
        if (!$(this).parent().hasClass('table-responsive')) {
            $(this).wrap('<div class="table-responsive"></div>');
        }
    });

    // Initialize popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'))
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl)
    });

    // Add keyboard shortcuts
    $(document).keydown(function(e) {
        // Alt + S to focus search
        if (e.altKey && e.keyCode === 83) {
            e.preventDefault();
            $('#cnr').focus();
        }
        // Alt + H to go home
        if (e.altKey && e.keyCode === 72) {
            e.preventDefault();
            window.location.href = '/';
        }
        // Alt + L to view all cases
        if (e.altKey && e.keyCode === 76) {
            e.preventDefault();
            window.location.href = '/cases';
        }
    });
}); 