function setTimeRemaining(){
    var seconds = parseInt((GUESTMEAL_TIME_LEFT/1000)%60)
        , minutes = parseInt((GUESTMEAL_TIME_LEFT/(1000*60))%60)
        , hours = parseInt((GUESTMEAL_TIME_LEFT/(1000*60*60))%24);

    hours = (hours < 10) ? "0" + hours : hours;
    minutes = (minutes < 10) ? "0" + minutes : minutes;
    seconds = (seconds < 10) ? "0" + seconds : seconds;

    var countdown_time = hours > 0 ? (hours + "h " + minutes + "m") : (minutes + "m " + seconds + "s");
    $('.time-left').html("Time left: " + countdown_time);
}

function setGuestmealPrice(){
    $('.current-price').html('$' + parseFloat(Math.round(GUESTMEAL_CURRENT_PRICE * 100) / 100).toFixed(2));
}

// "buy-container"
if(GUESTMEAL_TIME_LEFT.length > 0) {

    // Updating the actual evaulation 
    setGuestmealPrice();
    setInterval(function () {
        if (GUESTMEAL_TIME_LEFT > 0 && GUESTMEAL_CURRENT_PRICE > 0.00) {
            GUESTMEAL_CURRENT_PRICE = GUESTMEAL_CURRENT_PRICE - 0.01;
        }
        setGuestmealPrice();
    }, GUESTMEAL_RATE_OF_DECREASE);


    // Time left Code
    setTimeRemaining();
    setInterval(function () {
        GUESTMEAL_TIME_LEFT = (GUESTMEAL_TIME_LEFT >= 1000 ? GUESTMEAL_TIME_LEFT - 1000 : 0);
        setTimeRemaining();
    }, 1000);

} else {
    $('.buy-container').html('<h2>No Guestmeals Currently on the Market.</h2><h3>Please check again soon!</h3>');
}
