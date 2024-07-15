(function ($) {
    "use strict";

    // Preloader Js
    $(window).on('load', function () {
        $('#overlayer').fadeOut(1000);
        const img = $('.bg_img');
        img.css('background-image', function () {
            return ('url(' + $(this).data('background') + ')');
        });
    });

    $(document).ready(function () {

        if (document.querySelectorAll(".countdown-timer").length) {
            let counters = document.querySelectorAll(".countdown-timer");

            counters.forEach(function (counterElement) {
                let endDateString = counterElement.dataset.expireDate;
                // let endDate = new Date(endDateString);
                let now = new Date();

                // Parse the input date string using Moment.js
                let parsedDate = moment(endDateString, "MMM. DD, YYYY, h:mm a");

                let endDate = parsedDate.format("YYYY-MM-DDTHH:mm:ss");

                endDate = new Date(endDate);

                if (endDate > now) {
                    let myCountDown = new ysCountDown(endDate, function (remaining, finished) {
                        let days = remaining.totalDays;
                        let hours = remaining.hours;
                        let minutes = remaining.minutes;
                        let seconds = remaining.seconds;

                        let message = "";

                        if (finished) {
                            message = "Expired";
                        } else {
                            message += days + "d : ";
                            message += hours + "h : ";
                            message += minutes + "m : ";
                            message += seconds + "s";
                        }

                        counterElement.textContent = message;
                    });
                } else {
                    counterElement.textContent = "Expired";
                }
            });
        }

        if (document.querySelectorAll(".dashboard-expire-date").length) {
            let counters = document.querySelectorAll(".dashboard-expire-date");

            counters.forEach(function (counterElement) {
                let endDateString = counterElement.dataset.dashboardExpire;
                let parsedDate = moment(endDateString, "MMM. DD, YYYY, h:mmA");

                counterElement.textContent = parsedDate.format("M/D/YYYY")
            })
        }
        //New Countdown Starts
        if ($("#bid_counter26").length) {
            // If you need specific date then comment out 1 and comment in 2
            // let endDate = "2020/03/20"; //This is 1
            let endDate = (new Date().getFullYear()) + '/' + (new Date().getMonth() + 1) + '/' + (new Date().getDate() + 1); //This is 2
            let counterElement = document.querySelector("#bid_counter23");
            let myCountDown = new ysCountDown(endDate, function (remaining, finished) {
                let message = "";
                if (finished) {
                    message = "Expired";
                } else {
                    var re_days = remaining.totalDays;
                    var re_hours = remaining.hours;
                    message += re_days + "d  : ";
                    message += re_hours + "h  : ";
                    message += remaining.minutes + "m  : ";
                    message += remaining.seconds + "s";
                }
                counterElement.textContent = message;
            });
        }


        // Nice Select
        $('.select-bar').niceSelect();
        // counter
        $('.counter').countUp({
            'time': 2500,
            'delay': 10
        });
        // PoPuP
        $('.popup').magnificPopup({
            disableOn: 700,
            type: 'iframe',
            mainClass: 'mfp-fade',
            removalDelay: 160,
            preloader: false,
            fixedContentPos: false,

        });
        $("body").each(function () {
            $(this).find(".img-pop").magnificPopup({
                type: "image",
                gallery: {
                    enabled: true
                }
            });
        });
        // Faq
        $('.faq-wrapper .faq-title').on('click', function (e) {
            var element = $(this).parent('.faq-item');
            if (element.hasClass('open')) {
                element.removeClass('open');
                element.find('.faq-content').removeClass('open');
                element.find('.faq-content').slideUp(300, "swing");
            } else {
                element.addClass('open');
                element.children('.faq-content').slideDown(300, "swing");
                element.siblings('.faq-item').children('.faq-content').slideUp(300, "swing");
                element.siblings('.faq-item').removeClass('open');
                element.siblings('.faq-item').find('.faq-title').removeClass('open');
                element.siblings('.faq-item').find('.faq-content').slideUp(300, "swing");
            }
        });
        // Menu Dropdown Icon Adding
        $("ul>li>.submenu").parent("li").addClass("menu-item-has-children");
        // drop down menu width overflow problem fix
        $('.submenu').parent('li').hover(function () {
            var menu = $(this).find("ul");
            var menupos = $(menu).offset();
            if (menupos.left + menu.width() > $(window).width()) {
                var newpos = -$(menu).width();
                menu.css({
                    left: newpos
                });
            }
        });
        $('.menu li a').on('click', function (e) {
            var element = $(this).parent('li');
            if (element.hasClass('open')) {
                element.removeClass('open');
                element.find('li').removeClass('open');
                element.find('ul').slideUp(300, "swing");
            } else {
                element.addClass('open');
                element.children('ul').slideDown(300, "swing");
                element.siblings('li').children('ul').slideUp(300, "swing");
                element.siblings('li').removeClass('open');
                element.siblings('li').find('li').removeClass('open');
                element.siblings('li').find('ul').slideUp(300, "swing");
            }
        });
        // Scroll To Top
        var scrollTop = $(".scrollToTop");
        $(window).on('scroll', function () {
            if ($(this).scrollTop() < 500) {
                scrollTop.removeClass("active");
            } else {
                scrollTop.addClass("active");
            }
        });
        // Click event to scroll to top
        $('.scrollToTop').on('click', function () {
            $('html, body').animate({
                scrollTop: 0
            }, 500);
            return false;
        });
        // Header Bar
        $('.header-bar').on('click', function () {
            $(this).toggleClass('active');
            $('.overlay').toggleClass('active');
            $('.menu').toggleClass('active');
        });
        $('.overlay').on('click', function () {
            $(this).removeClass('active');
            $('.header-bar').removeClass('active');
            $('.menu').removeClass('active');
            $('.cart-sidebar-area').removeClass('active');
        });
        $('.cart-button, .side-sidebar-close-btn').on('click', function () {
            $(this).toggleClass('active');
            $('.overlay').toggleClass('active');
            $('.cart-sidebar-area').toggleClass('active');
        });
        $('.search-bar').on('click', function () {
            $('.search-form').toggleClass('active');
        });
        $('.remove-cart').on('click', function (e) {
            e.preventDefault();
            $(this).parent().parent().hide(300);
        });
        // Header Sticky Here
        var scrollPosition = window.scrollY;
        if (scrollPosition >= 1) {
            $(".header-section").addClass('active');
        }
        var header = $(".header-bottom");
        $(window).on('scroll', function () {
            if ($(this).scrollTop() < 1) {
                header.removeClass("active");
            } else {
                header.addClass("active");
            }
        });
        $('.tab ul.tab-menu li').on('click', function (g) {
            var tab = $(this).closest('.tab'),
                index = $(this).closest('li').index();
            tab.find('li').siblings('li').removeClass('active');
            $(this).closest('li').addClass('active');
            tab.find('.tab-area').find('div.tab-item').not('div.tab-item:eq(' + index + ')').hide(10);
            tab.find('.tab-area').find('div.tab-item:eq(' + index + ')').fadeIn(10);
            g.preventDefault();
        });
    });
})(jQuery);
