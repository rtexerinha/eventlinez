var mySwiper = new Swiper ('.swiper-container', {
	loop: false,
	slidesPerView: 1,
	spaceBetween: 15,
	pagination: {
        el: '.swiper-pagination',
	},

  	navigation: {
    	nextEl: '.swiper-button-next',
    	prevEl: '.swiper-button-prev',
  	},
	breakpoints: {
	    // 320: {
        //     slidesPerView: 1,
        // },
	    400: {
            slidesPerView: 1,
        },
		768: {
			slidesPerView: 3
		},
		920: {
			slidesPerView: 4
		}
	}
});