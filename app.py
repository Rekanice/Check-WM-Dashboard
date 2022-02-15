from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask.json import loads
from time import localtime, strftime, sleep
from datetime import datetime
from pytz import timezone
import os
import logging 
from turbo_flask import Turbo
import threading
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
import pandas as pd
from bokeh.plotting import figure, show
from bokeh.colors import named
from bokeh.io import output_file, output_notebook, show
from bokeh.transform import factor_cmap
from bokeh.models import PrintfTickFormatter
from bokeh.resources import CDN
import json
from bokeh.embed import json_item

# -----------------------------------------------------------------------------------------------------------------------------------------------

logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
turbo = Turbo(app)

# CHANGE to 'dev' when developing locally, 'prod' when deploying
ENV = 'dev'
if ENV == 'dev':
    app.debug = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+psycopg2://postgres:t1y8@localhost/idle_washer'
else:
    app.debug = False
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://npsdjgitlfrnxl:b099cb9e69553453a515c8f6125b060f4bc5c3af1f1cb584715d50c062b8517d@ec2-44-199-52-133.compute-1.amazonaws.com:5432/d8cg86isf8p6d4'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'], echo=True)

db = SQLAlchemy(app)

# -----------------------------------------------------------------------------------------------------------------------------------------------

# Database tables definition
class Washing_Machine(db.Model):

    # Create a table with these columns
    __tablename__ = 'washing_machine'
    id = db.Column(db.Integer, primary_key=True)            # Washing machine global ID
    college = db.Column(db.String, nullable=False)
    block = db.Column(db.String, nullable=False)
    location = db.Column(db.String, nullable=False)    
    room_index = db.Column(db.Integer, nullable=False)      # Position in the room, starting from leftmost side & increase in clockwise direction
    money_input = db.Column(db.Boolean, nullable=False)     # True=paper notes, False=coins
    is_working = db.Column(db.Boolean, nullable=False)      # True=working, False=rosak
    
    # Create an object with the table columns as its properties
    def __init__(self, id, location, room_index, money_input, is_working):
        self.id = id
        self.college = college
        self.block = block
        self.location = location
        self.room_index = room_index
        self.money_input = money_input
        self.is_working = is_working

    # This is not necessary. This prints the following statement when we print an instance of this class
    def __repr__(self):
        return f"This table has {self.id} washing machines in total."

class Sensor_Log(db.Model):

    # Create a table with these columns
    __tablename__ = 'sensor_log'
    timestamp = db.Column(db.DateTime, primary_key=True)   # Composite keys
    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.Time, nullable=False)
    wm_id = db.Column(db.Integer, db.ForeignKey('washing_machine.id'), primary_key=True)  # Composite keys
    in_use = db.Column(db.String, nullable=False)                      

    # Create an object with the table columns as its properties
    def __init__(self, timestamp, wm_id, in_use):
        self.timestamp = timestamp
        self.wm_id = wm_id
        self.in_use = in_use

    # This is not necessary. This prints the following statement when we print an instance of this class
    def __repr__(self):
        return f"The latest log: WM #{self.wm_id} is in_use={self.in_use} , at datetime={self.timestamp}."

# -----------------------------------------------------------------------------------------------------------------------------------------------

# Old Dashboard
@app.route("/olddashboard", methods=['GET'])
def home():
    return render_template('olddashboard.html')


# Update the Sensor Data variable every time before the home page is rendered
@app.context_processor
def injectSensorData():
    fetch_wm_id = 1
    fetched_latest_data = Sensor_Log.query.filter_by(wm_id=fetch_wm_id).order_by(Sensor_Log.timestamp.desc()).first()    #Just read as class object, insted of JSON object
    
    if fetched_latest_data.in_use == 'IDLE':
        gotLight = 0
    elif fetched_latest_data.in_use == 'IN USE':
        gotLight = 1

    return dict(
        wm_id = fetch_wm_id,
        gotLight = gotLight, 
        update_time = fetched_latest_data.timestamp.strftime("%Y %b %d, %a %I:%M %p")
    )

# Background updater thread that runs before a client connects for the 1st time
@app.before_first_request
def before_first_request():
    threading.Thread(target=update_sensor_data).start()

def update_sensor_data():
    with app.app_context():    
        while True:
            sleep(5)
            # Update the wm status (button colour) and the last update time
            turbo.push(turbo.replace(render_template('wm_update_time.html'), 'wm_time_text'))
            turbo.push(turbo.replace(render_template('wm_element.html'), 'wm_element'))


# -----------------------------------------------------------------------------------------------------------------------------------------------

# New dashboard 
@app.route("/", methods=['GET'])
def newdashboard():

    return render_template('newdashboard.html', resources=CDN.render())

# Below are the APIs URL routes used to serve the frontend webpage
# Return the heatmap plot of the last hour washing machine statuses
@app.route('/onehourago', methods=['GET', 'POST'])
def onehourago_plot():
    
    one_hour_ago_table, timeSet, wmIdSet = onehourago_data()
    heatmap_plot = make_heatmap(timeSet, wmIdSet, one_hour_ago_table)
    return json.dumps(json_item(heatmap_plot, "onehourago-heatmap"))

# Extract the one-hour-ago data from SQL table into a dataframe
def onehourago_data():

    sqlquery = "SELECT * FROM sensor_log WHERE timestamp IN (SELECT timestamp FROM sensor_log ORDER BY timestamp  DESC LIMIT 39) ORDER BY wm_id, timestamp"
    onehourlog_df = pd.read_sql_query(sqlquery, con=engine, index_col='timestamp')
    onehourlog_df.wm_id = onehourlog_df.wm_id.astype(str)
    onehourlog_df.in_use = onehourlog_df.in_use.astype(str)
    onehourlog_df.time = onehourlog_df.time.apply(lambda x: x.strftime("%H:%M"))
    
    # Get the unique values for the x-axis & yaxis labels, turn them into strings (required by Bokeh figure())
    timeSet = list(onehourlog_df["time"].unique())
    wmIdSet = reversed(onehourlog_df["wm_id"].unique())
    wmIdSet = list(map(str, wmIdSet))

    return onehourlog_df, timeSet, wmIdSet

# Put the plot-making process in a function
def make_heatmap(xSet, ySet, dataTable):

    p = figure(
           x_range=xSet, y_range=ySet,
           x_axis_location="above", width=610, height=210,
           tools="hover", toolbar_location=None,
           tooltips=[('time', '@time'), ('wm', '@wm_id'), ('status', '@in_use')]
        )

    p.yaxis[0].formatter = PrintfTickFormatter(format="wm %s")

    p.outline_line_color = None
    p.grid.grid_line_color = None
    p.axis.axis_line_color = None
    p.axis.major_tick_line_color = None
    p.axis.major_label_text_font_size = "13px"
    p.axis.major_label_standoff = 0
    p.axis.major_label_text_font = 'open sans pro'

    cmap = {
        'IDLE' : "dimgrey",
        'IN USE' : "orange"
    }
    p.rect(x="time", y="wm_id", width=1, height=1,
        source=dataTable, legend_field="in_use",
        fill_color= factor_cmap("in_use", list(cmap.values()), list(cmap.keys())),
        line_color='white', line_width=6
        )
    p.legend.orientation = "horizontal"
    p.legend.label_text_font_size = "14px"
    p.legend.label_text_font = 'open sans pro'
    p.add_layout(p.legend[0], 'above')
    
    return p 

# Return the current status of each washing machine in the location
@app.route('/currentstatus', methods=['GET', 'POST'])
def currentstatus_display():
    sqlquery = "SELECT * FROM sensor_log WHERE timestamp = (SELECT timestamp FROM sensor_log ORDER BY timestamp  DESC LIMIT 1)"
    currentstatus_df = pd.read_sql_query(sqlquery, con=engine)
    currentstatus_df = currentstatus_df[['wm_id', 'in_use']].set_index('wm_id')
    
    return json.dumps(currentstatus_df.to_dict())  # Output looks like this: {"in_use": {"1": "IN USE", "2": "IDLE", "3": "IDLE"}}
 
# Return the last datetime when the database was updated.
@app.route('/currentdatetime', methods=['GET', 'POST'])
def currentdatetime_data():
    sqlquery = "SELECT * FROM sensor_log WHERE timestamp = (SELECT timestamp FROM sensor_log ORDER BY timestamp  DESC LIMIT 1)"
    currentdt_df = pd.read_sql_query(sqlquery, con=engine)
    currentdt_dict = currentdt_df[['timestamp']].to_dict()
    currentdt = list( currentdt_dict['timestamp'].values() )[0]
    currentdt = currentdt.strftime("%b %d, %a %I:%M %p")
    
    return json.dumps(str(currentdt))  # Output looks like {"timestamp": {"0": "2022-02-11 10:00:00", "1": "2022-02-11 10:00:00", "2": "2022-02-11 10:00:00"}}
 
# -----------------------------------------------------------------------------------------------------------------------------------------------

if __name__ == '__main__':
    port = os.environ.get("PORT", 5000)             # Get port number of env at runtime, else use default port 5000
    app.run(debug=True, host='0.0.0.0', port=port)  # 0.0.0.0 port forwarding resolves the host IP address at runtime
 