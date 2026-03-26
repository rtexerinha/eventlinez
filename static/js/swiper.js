var swiper = new Swiper('.slider-banner', {
	slidesPerView: 1,
	centeredSlides: true,
	autoplay: {
		delay: 4000,
	},
	spaceBetween: 0, //it is only effective when slidesPerView >=2
	paginationClickable: true,
	pagination: {
		el: '.swiper-pagination-banner',
		clickable: true,
	},
	lazyLoading: true,
	// iOS 18: prevent Swiper from calling preventDefault on touchstart,
	// which blocks native page scroll on iPhone 16 / Safari 18
	touchStartPreventDefault: false,
	passiveListeners: true,
});


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
		// 400: {
		//     slidesPerView: 2,
		// },
		768: {
			slidesPerView: 3
		},
		920: {
			slidesPerView: 4
		}
	},
	// iOS 18: same fix — allow browser to handle vertical scroll natively
	touchStartPreventDefault: false,
	passiveListeners: true,
});