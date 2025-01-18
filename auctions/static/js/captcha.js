function loadRecaptchaScript() {
    const recaptchaScript = document.createElement('script');
    recaptchaScript.src = 'https://www.google.com/recaptcha/api.js?onload=onloadCallback&render=explicit';
    recaptchaScript.async = true;
    recaptchaScript.defer = true;
    document.head.appendChild(recaptchaScript);
}

window.onloadCallback = function () {
    loadRecaptchaScript();
};

document.querySelectorAll('.captcha_form').forEach(function (form) {
    form.addEventListener('submit', function (event) {
        event.preventDefault();

        const recaptchaResponse = grecaptcha.getResponse();
        const captchaMessage = form.querySelector('.captcha_message');

        if (recaptchaResponse.length === 0) {
            captchaMessage.classList.remove('hidden');
            captchaMessage.classList.add('block');
            captchaMessage.textContent = 'Please complete the reCAPTCHA';
        } else {
            captchaMessage.classList.remove('block');
            captchaMessage.classList.add('hidden');
            form.submit();
        }
    });
});
