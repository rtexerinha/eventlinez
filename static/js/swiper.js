if (typeof Swiper !== 'undefined') {
	if (document.querySelector('.slider-banner')) {
		var swiper = new Swiper('.slider-banner', {
			slidesPerView: 1,
			centeredSlides: true,
			autoplay: {
				delay: 4000,
			},
			spaceBetween: 0,
			paginationClickable: true,
			pagination: {
				el: '.swiper-pagination-banner',
				clickable: true,
			},
			lazyLoading: true,
			touchStartPreventDefault: false,
			passiveListeners: true,
		});
	}

	if (document.querySelector('.slider-card')) {
		var mySwiper = new Swiper('.slider-card', {
			loop: false,
			slidesPerView: 1.5,
			spaceBetween: 30,
			pagination: {
				el: '.swiper-pagination',
			},
			navigation: {
				nextEl: '.swiper-button-next',
				prevEl: '.swiper-button-prev',
			},
			breakpoints: {
				768: {
					slidesPerView: 3
				},
				920: {
					slidesPerView: 4
				}
			},
			touchStartPreventDefault: false,
			passiveListeners: true,
		});
	}
}
