document.addEventListener('DOMContentLoaded', function() {
    // Initialize all carousels on the page
    const carousels = document.querySelectorAll('.more-to-explore-carousel');
    
    carousels.forEach(carousel => {
        const carouselTrack = carousel.querySelector('.explore-carousel-track');
        const prevBtn = carousel.querySelector('.btn-carousel-prev');
        const nextBtn = carousel.querySelector('.btn-carousel-next');
        const carouselContainer = carousel.querySelector('.explore-carousel-container');
        
        // Calculate item width including margin
        const firstItem = carousel.querySelector('.carousel-item');
        if (!firstItem) return;
        
        const itemWidth = firstItem.offsetWidth;
        const gap = 15;
        
        nextBtn.addEventListener('click', () => {
            carouselContainer.scrollBy({
                left: itemWidth + gap,
                behavior: 'smooth'
            });
        });
        
        prevBtn.addEventListener('click', () => {
            carouselContainer.scrollBy({
                left: -(itemWidth + gap),
                behavior: 'smooth'
            });
        });
        
        // Hide/show buttons based on scroll position
        carouselContainer.addEventListener('scroll', function() {
            const maxScroll = carouselTrack.scrollWidth - carouselContainer.clientWidth;
            
            if (carouselContainer.scrollLeft <= 0) {
                prevBtn.style.opacity = '0.5';
                prevBtn.style.cursor = 'not-allowed';
            } else {
                prevBtn.style.opacity = '1';
                prevBtn.style.cursor = 'pointer';
            }
            
            if (carouselContainer.scrollLeft >= maxScroll - 5) {
                nextBtn.style.opacity = '0.5';
                nextBtn.style.cursor = 'not-allowed';
            } else {
                nextBtn.style.opacity = '1';
                nextBtn.style.cursor = 'pointer';
            }
        });
        
        // Initialize button states
        prevBtn.style.opacity = '0.5';
        prevBtn.style.cursor = 'not-allowed';
        
        // Check if next button should be disabled initially
        if (carouselTrack.scrollWidth <= carouselContainer.clientWidth) {
            nextBtn.style.opacity = '0.5';
            nextBtn.style.cursor = 'not-allowed';
        }
    });
});