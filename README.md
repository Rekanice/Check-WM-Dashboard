# Check-WM-Dashboard
This repository is exclusively for milestone 5. It contains the necessary files to run the Flask dashboard app for the Check Washing Machine application. For more info about the prior milestones and the development of this project, refer to the parent repository [here](https://github.com/Rekanice/swe-G2-iot-project).


### Steps to reproduce the Flask dashboard app in your local machine. 

1. `git clone` this repository into a location of your choice.


2. Open the cloned folder in a code editor (eg. Visual Studio Code) or move the folder path in your terminal.


3. Create a python virtual environment for the app. Run the code below according to your system, to activate a virtual environment. You should see a (venv) in the front of your current terminal line after activating the virtual environment.
  
  In Linux terminal:
  ```
  sudo apt install -y python3-venv 
  virtualenv venv
  source venv/bin/activate
  ```
  In Windows powershell
  ```
  virtualenv venv
  cd venv\Scripts
  .\activate
  cd ..\..
  ```
  
</br>

4. Install the necesary modules in the virtual environment
 ```
 pip install requirements.txt
 ```
 
 </br>
 
5. Install PostgresSQL database application 
- Install the 13.6 version [here](https://www.enterprisedb.com/downloads/postgres-postgresql-downloads)
- Follow the tutorial in these articles for the initial setup of the database. [Windows](https://www.postgresqltutorial.com/install-postgresql/) OR [Linux](https://www.postgresqltutorial.com/install-postgresql-linux/), and then [this](https://www.postgresqltutorial.com/connect-to-postgresql-database/).

</br>

6. In the pgAdmin 4, create a new database called `idle_washer` as shown in the image.
  ![alt text](https://github.com/Rekanice/swe-G2-iot-project/blob/4df836f737839fc081583b6752bc731de4cf2c07/create_pgdb.png)

</br>

7. Update the new database uri based on your database credentials. Edit this line of code in `app.py` without the `[]` brackets:
  ```
  ENV = 'dev'
  if ENV == 'dev':
    app.debug = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+psycopg2://postgres:[ur_password_to_postgres_db]@localhost/idle_washer'
  ```

</br>

8. Go to your Flask app terminal and initialize the tables in the database by running the code below. This creates the tables in the idle_washer database. 
 ```
 python
 >>> from app.py import db
 >>> db.create_all()
 >>> exit()
 ```
 You can check by looking into here: 
 
 ![alt text](https://github.com/Rekanice/swe-G2-iot-project/blob/4df836f737839fc081583b6752bc731de4cf2c07/init_db_tables.png)
 
</br>

9. Download these csv files for the data for each database table:
  - washing_machine : [washing_machine_db.csv]()
  - sensor_log : [random_sensor_log_db.csv](https://github.com/Rekanice/swe-G2-iot-project/blob/master/random_sensor_log_db.csv)

</br>

10. Go to the tables in the postgres database, and right click each table and import the csv data into the table. Follow the settings shown in the image.
  - ![alt text](https://github.com/Rekanice/swe-G2-iot-project/blob/4df836f737839fc081583b6752bc731de4cf2c07/import_csvdata1.png)
  - ![alt text](https://github.com/Rekanice/swe-G2-iot-project/blob/4df836f737839fc081583b6752bc731de4cf2c07/import_csvdata2.png)

</br>

11. Go to the Flask app again, and run app.py. Click the link that appears after a moment. You should be able to access the dashboard.
  Navigation Guide:
  - http://192.168.1.107:5000/ --> New dashboard for milestone 5
  - http://192.168.1.107:5000/olddashboard --> Old dashboard for milestone 4

