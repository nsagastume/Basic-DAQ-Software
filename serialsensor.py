import os
import time
import serial
from datetime import datetime
import driver_telemetry
from mercury_telemetry_pipeline import Pipeline
import datapoint
from formulas import Formulas
import formulas
from concurrent.futures import ThreadPoolExecutor
import concurrent.futures
from thermocouple import Thermocouple
from datapoint import Datapoint
SERIAL_ARDUINO_COUNT = 0  # hard coded value for now will determine how many arduinos there are
ENABLE_THERMOCOUPLE = True

def collect_data(serial_in, formula_calc, mercury_telemetry_pipeline, log):
    start_time = time.time() * 1000
    while(time.time() * 1000 <= start_time + 1000 * 60):  # Condition for when to stop the program currently 60 seconds
        output = parse_serial(serial_in, formula_calc, mercury_telemetry_pipeline)
        if output != "" and output is not None and ord(output[0]) != 0:
            log.write(bytes(output, 'utf-8').decode('utf-8', 'ignore') + "\n")
    serial_in.close()

def collect_temperatures(formula_calc, mercury_telemetry_pipeline, log):
    thermocouple = Thermocouple()
    start_time = time.time() * 1000
    while (time.time() * 1000 <= start_time + 1000 * 60):  # Condition for when to stop the program currently 60 seconds
        temperature = thermocouple.getTemperature()
        data = Datapoint(formulas.CVT_TEMP, "CVT Temperature", 1, ["temperature"], [temperature], "C", time.time() * 1000 * 1000 - start_time * 1000)
        formula_calc.apply_calculation(data)
        output = str(data)
        print(output)
        driver_telemetry.send_data(data)
        mercury_telemetry_pipeline.send_packet(data)
        log.write(output + "\n")



def parse_serial(serial_in, formula_calc, mercury_telemetry_pipeline):
    raw = serial_in.readline()
    output = ""
    try:  # the try block is here because the serial stream can sometimes have extraneous bytes that cant be converted to plain text such as 00, 0A, etc.
        output = raw.decode()  # decode the binary stream
        output = output.strip()  # removing extra spaces and LFs from serial stream
        if output[0:3] == "///":  # Checking for three character signature in the beginning of each serial line to tell the parser what the purpose of the input is
            output = ""  # nothing is printed
        elif output[0:3] == "###":
            output = "INFO: " + output[3:]  # info
            print(output)
            mercury_telemetry_pipeline.send_log(output)
        elif output[0:3] == "!!!":
            output = "ERROR: " + output[3:]  # error
            print(output)
            mercury_telemetry_pipeline.send_log(output)
        elif output[0:3] == "$$$":
            error = False
            data = None
            try:
                data = datapoint.get_datapoint_from_arduino_raw(output)
            except Exception as e:
                print(e)
                error = True
            if (error == False):
                formula_calc.apply_calculation(data)
                output = str(data)
                print(output)
                driver_telemetry.send_data(data)
                mercury_telemetry_pipeline.send_packet(data)
        else:
            print(output)  # unmarked serial input
    except UnicodeDecodeError:  # serial decode didnt work
        output = ""
    return output

def main():

    now = datetime.now()
    mercury_telemetry_pipeline = Pipeline()
    log = open(os.getcwd()+"/datalogs/serialdata_" + now.strftime("%m%d%Y_%H-%M-%S") + ".txt", "x")  # timestamping the text file and making a new log
    ## serial.Serial('/dev/ttyUSB0', 9600, timeout=1)
    log.write("Arduino data obtained from USB connection on " + now.strftime("%m/%d/%Y %H:%M:%S")+"\n\n")
    log.write("DAQ: Initializing " + str(SERIAL_ARDUINO_COUNT) + " Arduino(s)\n")
    print("DAQ: Initializing " + str(SERIAL_ARDUINO_COUNT) + " Arduino(s)")
    mercury_telemetry_pipeline.send_log("DAQ: Initializing " + str(SERIAL_ARDUINO_COUNT) + " Arduino(s)")
    serial_inputs = [serial.Serial('/dev/ttyUSB' + str(i), 9600, timeout=1) for i in range(SERIAL_ARDUINO_COUNT)]  # creates SERIAL_ARDUINO_COUNT serial inputs
    log.write("DAQ: Successfully Initialized " + str(SERIAL_ARDUINO_COUNT) + " Arduino(s)\n")
    print("DAQ: Successfully Initialized " + str(SERIAL_ARDUINO_COUNT) + " Arduino(s)")
    mercury_telemetry_pipeline.send_log("DAQ: Successfully Initialized " + str(SERIAL_ARDUINO_COUNT) + " Arduino(s)")
    """Each serial in represents an arduino plugged in VIA USB. Each arduino requires a separate serial instance"""
    # serial_in2 = serial.Serial('/dev/ttyUSB1', 9600, timeout=1)
    formula_calc= Formulas()
    log.write("Initializing Formulas\n")
    print("Initializing Formulas")
    mercury_telemetry_pipeline.send_log("Initializing Formulas")
    executor = ThreadPoolExecutor(max_workers=SERIAL_ARDUINO_COUNT)
    futures = []
    for serial_in in serial_inputs:
        args = [serial_in, formula_calc, mercury_telemetry_pipeline, log]
        futures.append(executor.submit(collect_data, *args))

    if (ENABLE_THERMOCOUPLE):
        args = [formula_calc, mercury_telemetry_pipeline, log]
        futures.append(executor.submit(collect_temperatures, *args))

    concurrent.futures.wait(futures)
    time.sleep(2)
    print("DAQ Program exiting with code 0")
    log.write("DAQ Program exiting with code 0\n")
    mercury_telemetry_pipeline.send_log("DAQ Program exiting with code 0")
    log.close()
    exit()

main()
