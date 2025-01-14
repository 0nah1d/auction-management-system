document.getElementById('contact_form').addEventListener('submit', function (event) {
    event.preventDefault();

    var recaptchaResponse = grecaptcha.getResponse();
    var captchaMessage = document.getElementById('captcha_message');

    if (recaptchaResponse.length === 0) {
        captchaMessage.classList.remove('hidden');
        captchaMessage.classList.add('block');
        captchaMessage.textContent = 'Please complete the reCAPTCHA';
    } else {
        captchaMessage.classList.remove('block');
        captchaMessage.classList.add('hidden');
        this.submit();
    }
});