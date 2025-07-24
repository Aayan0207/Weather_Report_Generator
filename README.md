# Weather Report Generator
#### Video Demo:  https://youtu.be/WYpnTkNvofY
#### Description:

The project is in essence a Weather Report Generator which takes as user input a,
 i. Location on the globe
 ii. A date
 and optionally,
 iii. A second date (to facilitate the generation of a range of reports for the given location)

Once the user request is verified and the program has executed, a PDF is generated containing the latest weather report of
the provided location for the provided date/dates.

The Python program is broadly divided into four sub-programs to generate the PDF in the following order:

##### 1. Prompt Parsing

The 2 or 3 arguments provided by the user as a prompt are parsed and verified to identify the request/requests made.
The location is uniform for all PDFs to be generated.
As per the date/dates provided, each one is assessed and categorized into one of 3 types of reports:
i. If the date is the current date, then a current weather report is generated for the location.
ii. If the date is in the future from the current date, a forecast weather report is generated.
iii. Finally, if the date precedes the current date, then a historical weather report is generated.

As per the type of report, a corresponding API request is made to Weather API's servers.
Weather API: https://www.weatherapi.com/

On the current API key, a maximum weather forecast of 2 days ahead is allowed, and a historical report of up to 7 days prior.

##### 2. Data Extraction and Representation

Once the data from the API call has been received, it needs to be properly represented.
For that, a class called Day was introduced with instance, static, and class methods.
The class is capable of extracting and aptly representing data as per the type of report to be generated, given the date.

##### 3. Graph Generation

As per the data stored in the class objects and using concepts from Object-Oriented Programming, hourly data is represented
with the help of graphs for a particular day.

The graphs generated are as follows:
 i. Hourly Weather Condition
 ii. Hourly Temperature (°C/°F)
 iii. Hourly Wind Speed and Direction (kph/mph)
 iv. Hourly Gust Speed (kph/mph)
 v. Hourly Pressure (mb)
 vi. Hourly Chances of Precipitation and Snowfall (%)
 vii. Hourly amount of Precipitation and Snowfall (cm and mm)
 viii. Hourly Humidity and Cloud Cover (%)
 ix. Hourly Dewpoint (°C/°F)
 x.  Hourly Visibility (km/miles)

 If the report type is either current or forecast
 xi. Hourly UV Index and AQI Index

 Else if the report is of type historical
 xi. Hourly UV

The current API key doesn't return the AQI index for historical reports.

##### 4. PDF Generation

Finally, when both the data from the API is present and the graphs are generated, all the information is grouped together
into one PDF file per date and saved in the current working directory.

##### Modules used

i. datetime:
 Converting date strings to datetime dates for a higher level of control and functionality, such as adding dates and
 comparing them.

ii. sys:
 Directly getting user input from the terminal when beginning program execution and exiting/terminating the program in
 case of any error with a proper exit message.

iii. re:
 Using the search function for a higher level of pattern matching and string verification using Regular Expressions.

iv. os:
 Dynamically generate the path for the final PDF file as per the current working directory, as well as create the plots
 directory upon program execution and user request verification to store generated graphs.

v. shutil:
 Specifically, the rmtree method to delete the plots directory once the PDF file is generated.

vi. matplotlib
 Main module used for generating graphs

vii. numpy:
 Specifically, the array method is used to help with graph generation.

viii. io:
 Specifically, the BytesIO method for storing the requested condition text image in memory without actually saving the
 file.

ix. PIL:
 To help operate the graph image files.

x. termcolor:
 Specifically, the colored method to print colored text to the terminal

xi. emoji:
 Specifically, the emojize method to print emojis to the terminal given their character code

xii. time:
 Specifically, the sleep function adds a delay for the loading... animations to make them smoother.

xiii. requests:
 Specifically, the get function is used to obtain information from a URL.
 
xiv. fpdf
 The main library used to generate the PDF and save it.
