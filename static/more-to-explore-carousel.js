document.addEventListener('DOMContentLoaded', function() {
  const carouselTrack = document.querySelector('.explore-carousel-track');
  const prevBtn = document.querySelector('.btn-carousel-prev');
  const nextBtn = document.querySelector('.btn-carousel-next');
  const carouselContainer = document.querySelector('.explore-carousel-container');
  
  const itemWidth = document.querySelector('.carousel-item').offsetWidth;
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
});