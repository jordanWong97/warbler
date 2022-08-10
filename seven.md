How is the logged in user being kept track of?

Logged in user is being kept track with g.user, which is a global object.

What is Flask's g object?

A global object provided by flask to keep track of global variables for current user session. These global variables can be accessed through Jinja templates as well so we don't need to instantiate the CSRF form class for each post request.

What is the purpose of add_user_to_g?

First we check if there is a current user in the session, and if there is, we grab user-id which gives us the user instance. Then we assign the current user instance to our global variable.

What does @app.before_request mean?

Registers a function to run before each request. With this @app.before_request, we can instantiate the global user and csrf form and assign them to g variables so we can access them throughout the request cycle.

