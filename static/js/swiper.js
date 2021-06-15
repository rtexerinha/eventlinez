var mySwiper = new Swiper ('.swiper-container', {
	loop: false,
	slidesPerView: 1,
	spaceBetween: 15,
	pagination: {
        el: '.swiper-pagination',
	},

  	navigation: {
		//  nextEl: '.swiper-button-next-unique',
    	// prevEl: '.swiper-button-prev-unique'
    	nextEl: '.swiper-button-next',
    	prevEl: '.swiper-button-prev',
  	},
	breakpoints: {
	    // 320: {
        //     slidesPerView: 2,
        // },
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