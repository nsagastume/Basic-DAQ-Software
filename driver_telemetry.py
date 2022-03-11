#This module will be used to call methods which display stuff on the Driver HUD. We can also do some calculations in here such as deriving new quantities and displaying them.
#One thing we must note is this is specifically for the offline stuff. If you are looking to fix data sent to the pits, see mercury-telemetry
DOF9 = 0
STEERING_ANGLE = 1
HALL_EFFECT = 2
FUEL = 3
CVT_TEMP = 4
GPS = 5
## others will defined with different identification

"""
data: [(int ID), (string Name), (int num_outputs), (list<string> comma_series_names), (list<double> comma_delimited outputs), (list<string> comma_delimited_units), (double time)]
"""

## Each method other than send_data will be

def display_speed(speed):
    print("I am going " + str(speed) + " mph!")
    # TODO call method to display speed on speedometer


def display_steering(angle):
    print("I am steering at a " + str(angle) + " degree angle!")
    # TODO call method to display steering angle (if applicable)


# TODO make functions for all of the quantities we want the driver to see during the race

def send_data(ID, name, num_outputs, series_names, outputs, units, time):
    if ID == HALL_EFFECT:
        display_speed(outputs[0])
    elif ID == STEERING_ANGLE:
        display_steering(outputs[0])

