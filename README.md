# CS50 Final Project - Recipe Swap
Recipe Swap is a web application that allows you to swap recipes with your friends or colleagues. Each person/participant would receive someone else's recipe via email. When the food in the recipe is cooked, each person may upload photos showing his/her cooking process and/or the final product and post any desired comments.

&nbsp;

## Description of the Project
Technologies used to create this project include Python, HTML, CSS, Flask, Jinja, SQLite3, and JavaScript. There were various files used to construct this project, which will all be detailed below in approximately chronological order.

&nbsp;

### **layout.html**
This file is the basis for all the other HTML files. It specifies which version of Bootstrap all CSS and JavaScript code should use. It specifies which emoji and text to use in the title of each HTML page.

The navigation bar is built on this page, which shows different options depending on if the user is logged in. Lastly, it specifies the style for flashed messages and containers for each page.

&nbsp;

### login.html
By default, the user will be directed to this page to input their username and password to log in. If user is not yet registered, they should register first by clicking on "Register" at the top right of the navigation bar.

&nbsp;

### register.html
The user can register on this page by inputting a username that isn't already in the database, entering the same password twice, and entering their first name. Password must be 8-32 characters, have at least one uppercase character, have at least one lowercase character, and have at least one special character.

&nbsp;

### add.html
After registering or logging in, the user will be directed to a page to add as many people/participants as they desire to participate in the Recipe Swap. An e-mail address should be provided for each participant.

&nbsp;

### delete.html
On this page, the user may delete participants from the Recipe Swap.

&nbsp;

### swap.html
After the user has added at least three participants, they can click on "Recipe Swap" in the upper left side of the navigation bar and be directed to the home page. Each participant should submit a recipe name and file to the user. Then, the user will input that information on this page. Only one file is allowed per person, and providing a webpage or link to the recipe is optional. If a webpage file is saved in ".mhtml" format, it can be uploaded as a file.

Once all information on this page is populated, the user should click on the "Swap Recipes!" button and an email will be sent out to each participant describing which recipe they were assigned at random.

&nbsp;

### index.html
If the user tries to click on "Assignments" in the upper left of the navigation bar prior to swapping recipes, an error message will pop up. Once the user does swap recipes, they will be redirected to this page and you can see everyone's recipe assignments.

After participants finish cooking their assigned recipes, either the user or each participant can upload photos of their recipes and post comments to this page. Multiple photos can be selected to show how the entire cooking process worked out.

Upon clicking the "Upload Photo(s), Save Comment(s) button below the table, all photos selected will upload to the server and display in the row(s) they were selected for. Any comments posted will remain, until modified later.

If the user wishes to repeat a Recipe Swap for the participants, they should click on the "Clear Assignments" button below the table, and click "Clear" for the pop-up message that comes up. Trying to swap recipes before clearing assignments will redirect the user back to the Assignments page and pop up an error message.

&nbsp;

### change.html
This page allows the user to change their password by entering their old password once and new password twice.

&nbsp;

### apology.html
The user will be redirected to this page with an error message if they encounter an error, such as trying to add a participant with an email that already exists in the database.

&nbsp;

## **app.py**
app.py imports many libraries enabling functions for the user to register, log in, validate emails and passwords, send emails, randomize recipe assignments, etc. An API key must be set before running this web app.

Two folders lie in the /static directory to take in uploaded recipe files and photos, respectively. They are configured, and each file has a limit on size. Functions are set up to determine if an uploaded file is valid, based on its extension.

&nbsp;

### **swap() function**
This function communicates with the swap.html file. If retrieving data from the homepage, a blank table will be shown if at least three participants have been added.

Pertinent data will be selected from tables generated in SQLite3, and some of it will be appended to lists to make data easier to call out.

Upon sending data to the server, any files from the upload folder will be cleared as it implies the user is trying to swap recipes amongst participants with new files. Each file will be inspected to verify it has a valid name and extension. If any file is invalid, an error message will generate and recipes will not be swapped. If all files are valid, they will be secured and saved to the "documents" folder in the Final Project directory.

File names with certain special characters are altered upon saving to the upload folder, upon saving the uploaded file names to a list, code is present to alter those file names in the same way as when they were saved to the upload folder.

For a certain account, date and time libraries were imported so the first Friday of every month would be displayed in each email message.

Logic is implemented such that each participant receives a recipe different from the one they submitted. Lists are populated asynchronously such that the recipe names and links (if applicable) line up with the file names submitted, and they can all be included in the same email to each participant.

MIMEBase is used to read and attach the recipe file to each email and set up the sender address, receiver address, subject, and message body.

Emails can only be sent from and to gmail addresses, but if you wanted to send to an outlook address, you would just change all instances of 'smtp.gmail.com' to 'smtp.outlook.com'.

Lastly, the SQLite3 "recipes" table will be cleared before all pertinent data is inserted into the table. Any photos of food uploaded from previous recipe swaps will also be cleared.

&nbsp;

### add() function
This function communicates with the add.html page. It validates a person's name and email address using regular expressions. An error message will generated if the name or email already exists in the database.

&nbsp;

### delete() function
This function communicates with the delete.html page. At least one participant must be in the database to access this page.

&nbsp;

### **index() function**
This function communicates with the index.html page. If retrieving data, a blank table will show if no photos have been uploaded yet and no comments have been posted.

Upon sending data to the server, the function checks if each participant has uploaded at least one photo already. If not, it will take valid photo(s) that were selected, upload them to a folder in the Final Project directory, and display them on the webpage.

At the same time, comments can be posted or edited as well. They will display on the webpage until modified and saved again.

A different message will pop up depending on if an error was generated, only photo(s) were uploaded, only comment(s) were updated, or if both photo(s) were uploaded and comment(s) were updated.

&nbsp;

### clear() function
This function does not comunicate with any HTML page. If the "Clear Assignments" button is clicked on the Assignments page, all recipe assignments will be cleared and the user will be able to faciliate the Recipe Swap once again.

&nbsp;

### login() function
This function communicates with the login.html page. A username and password combination that has already been registered must be submitted for the login to be successful.

&nbsp;

### logout() function
This function does not comunicate with any HTML page. Upon clicking the Log Out text on the top right of the navigation bar, the user will be logged out.

&nbsp;

### register() function
This function communicates with the register.html page. A unique username must be provided, and a password consisting of 8-32 characters, a combination of uppercase and lowercase characters, and at least one special character must be provided twice. A regular expression is used to check this.

&nbsp;

### change() function
This function communicates with the change.html page. The user's old password must be provided, and a new password is checked for matching and validity using the same regular expression as the register() function used.

&nbsp;

### helpers.py
helpers.py imports libraries enabling functions for routing, requests, and wrapping of functions. It sets up the template for an apology message and decorates routes to require login.
