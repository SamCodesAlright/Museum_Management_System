document.addEventListener("DOMContentLoaded", function () {
  // Select all carousel containers
  const carousels = document.querySelectorAll('.carousel-container');

  carousels.forEach((carousel) => {
    const track = carousel.querySelector(".carousel-track");
    const slides = Array.from(carousel.querySelectorAll(".carousel-slide"));
    const dots = Array.from(carousel.querySelectorAll(".carousel-dot"));
    const nextBtn = carousel.querySelector(".carousel-arrow.next");
    const prevBtn = carousel.querySelector(".carousel-arrow.prev");

    const slideWidth = slides[0].getBoundingClientRect().width;
    let currentIndex = 0;
    let maxVisibleSlides = 3;

    function updateMaxVisibleSlides() {
      if (window.innerWidth < 768) {
        maxVisibleSlides = 1;
      } else if (window.innerWidth < 992) {
        maxVisibleSlides = 2;
      } else {
        maxVisibleSlides = 3;
      }
    }

    function updateCarousel() {
      updateMaxVisibleSlides();
      const offset = -currentIndex * (slideWidth + 20);
      track.style.transform = `translateX(${offset}px)`;

      // Update dots
      dots.forEach((dot, index) => {
        dot.classList.toggle("active", index === currentIndex);
      });

      // Disable/enable navigation buttons
      prevBtn.disabled = currentIndex === 0;
      nextBtn.disabled = currentIndex >= slides.length - maxVisibleSlides;
    }

    function moveToSlide(index) {
      if (index >= 0 && index <= slides.length - maxVisibleSlides) {
        currentIndex = index;
        updateCarousel();
      }
    }

    function nextSlide() {
      if (currentIndex < slides.length - maxVisibleSlides) {
        currentIndex++;
        updateCarousel();
      }
    }

    function prevSlide() {
      if (currentIndex > 0) {
        currentIndex--;
        updateCarousel();
      }
    }

    // Event listeners
    nextBtn.addEventListener("click", nextSlide);
    prevBtn.addEventListener("click", prevSlide);

    dots.forEach((dot, index) => {
      dot.addEventListener("click", () => moveToSlide(index));
    });

    // Initialize
    updateMaxVisibleSlides();
    updateCarousel();
  });

  // Update all carousels on resize
  window.addEventListener("resize", function() {
    carousels.forEach(carousel => {
      // You might need to trigger the update for each carousel
      // The event listeners inside each carousel will handle it
    });
  });
});

