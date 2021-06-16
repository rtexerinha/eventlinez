var mySwiper = new Swiper ('.swiper-container', {
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