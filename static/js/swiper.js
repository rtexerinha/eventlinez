var swiper = new Swiper('.slider-banner', {
    slidesPerView: 1,
	  centeredSlides: true,
	autoplay: {
    delay: 2000,
  },
    spaceBetween: 0, //it is only effective when slidesPerView >=2
    paginationClickable: true,
	pagination: {
        el: '.swiper-pagination-banner',
		clickable: true,
	},
    lazyLoading: true,
});


var mySwiper = new Swiper ('.slider-card', {
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
	}
});