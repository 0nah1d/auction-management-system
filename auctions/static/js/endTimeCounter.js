function updateCountdown() {
    const countdownDivs = document.querySelectorAll(".countdown-timer:not(.expired)");
    const now = moment().tz("Asia/Dhaka");

    countdownDivs.forEach((countdownDiv) => {
        const expireDateStr = countdownDiv.getAttribute("data-expire-date");

        const endTime = moment.tz(expireDateStr, "MMM. D, YYYY, h:mm a", "Asia/Dhaka");

        if (!endTime.isValid()) {
            countdownDiv.textContent = "Invalid Date";
            countdownDiv.classList.add("expired");
            return;
        }

        const duration = moment.duration(endTime.diff(now));

        if (duration.asMilliseconds() <= 0) {
            countdownDiv.textContent = "EXPIRED";
            countdownDiv.classList.add("expired");
        } else {
            const days = Math.floor(duration.asDays());
            const hours = duration.hours();
            const minutes = duration.minutes();
            const seconds = duration.seconds();

            countdownDiv.textContent = `${days}d ${hours}h ${minutes}m ${seconds}s`;
        }
    });
}

setInterval(updateCountdown, 1000);
updateCountdown();
