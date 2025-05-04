// Modal functions
function openModal(modalId) {
    const modal = new bootstrap.Modal(document.getElementById(modalId));
    modal.show();
}

function closeModal(modalId) {
    const modal = bootstrap.Modal.getInstance(document.getElementById(modalId));
    modal.hide();
}

// Close modal when clicking outside content
document.addEventListener('click', function (event) {
    if (event.target.classList.contains('modal')) {
        const activeModal = document.querySelector('.modal.show');
        if (activeModal) {
            const modal = bootstrap.Modal.getInstance(activeModal);
            modal.hide();
        }
    }
});

// Keyboard navigation for modals
document.addEventListener('keydown', function (event) {
    if (event.key === 'Escape') {
        const activeModal = document.querySelector('.modal.show');
        if (activeModal) {
            const modal = bootstrap.Modal.getInstance(activeModal);
            modal.hide();
        }
    }
});

// Animation on scroll
document.addEventListener('DOMContentLoaded', function () {
    const animatedElements = document.querySelectorAll('.fade-in');

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.animationPlayState = 'running';
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.1 });

    animatedElements.forEach(element => {
        observer.observe(element);
    });
});

// Image placeholder replacement (for demo purposes)
document.addEventListener('DOMContentLoaded', function () {
    const placeholderImages = document.querySelectorAll('img[src^="/api/placeholder"]');

    placeholderImages.forEach(img => {
        const src = img.getAttribute('src');
        const dimensions = src.split('/').slice(-2);
        const width = dimensions[0];
        const height = dimensions[1];

        // Replace with actual placeholder service
        img.src = `https://picsum.photos/${width}/${height}?random=${Math.floor(Math.random() * 1000)}`;
        img.alt = img.alt || 'Exhibition item';
    });
});