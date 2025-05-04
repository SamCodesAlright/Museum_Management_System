document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.read-more-link').forEach(link => {
        const container = link.closest('.description-text');
        const shortText = container.querySelector('.short-text');
        const fullText = container.querySelector('.full-text');
        
        // Initialize link text
        link.textContent = '... read more';
        
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const isExpanded = fullText.style.display === 'inline';
            
            // Toggle visibility
            shortText.style.display = isExpanded ? 'inline' : 'none';
            fullText.style.display = isExpanded ? 'none' : 'inline';
            
            // Update link text (only change the action word)
            link.textContent = isExpanded ? '... read more' : 'read less';
        });
    });
});