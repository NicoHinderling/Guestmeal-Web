$(document).ready(function() {
    var lock = new Auth0Lock(AUTH0_CLIENT_ID, AUTH0_DOMAIN, {
        auth: {
          redirectUrl: AUTH0_CALLBACK_URL
        },
        theme: {
            logo: '/public/img/guestmeal-logo.png',
            primaryColor: 'green'
        },
        languageDictionary: {
            title: "Guestmeal Login"
        },
        additionalSignUpFields: [{
            name: "first_name",
            placeholder: "Enter your first name",
        }, {
            name: "last_name",
            placeholder: "Enter your last name",
        }]
     });

    $('.auth0-login-button').click(function(e) {
      e.preventDefault();
      lock.show();
    });

    $('.home-buy-button').click(function(e) {
        if (userLoggedIn) {
            console.log("You are logged in. TODO: ACTUALLY BUYING.... ");
        } else {
          e.preventDefault();
          lock.show();
        }
    });
});
