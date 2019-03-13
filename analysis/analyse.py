import argparse
import os
import sys
import time
import re
from datetime import timedelta

SECONDS_PER_TOPIC = 7 * 60


def analyse_app_log(source):
    with open(source) as f:
        queries = []
        num_clicked = 0
        num_relevant = 0

        lines = f.readlines()

        # Loop over each line
        for line in lines:
            z = re.match("\d{4}\-\d{2}\-\d{2}\s(\d{2}:\d{2}:\d{2}).\d{6}:\s(\w*?\s\w*?):\s(.*?)$", line)
            if not z:
                print("No match at line: ", line)
                continue
            groups = z.groups()
            time = groups[0]
            action = groups[1].split(" ")
            value = groups[2]

            if action[0] == "Entered":
                queries.append(value)
                continue

            if action[0] == "Clicked":
                num_clicked = num_clicked + 1
                continue

            if action[0] == "Marked":
                if action[1] == "relevant":
                    num_relevant = num_relevant + 1
                else:
                    num_relevant = num_relevant - 1

        # End of lines

        num_queries = len(queries)

        return {
            "num_queries": num_queries,
            "num_marked": num_relevant,
            "num_clicked": num_clicked
        }


def analyse_keylog(source):
    with open(source) as f:
        num_key_errors = 0
        num_chars = 0
        num_enters = 0
        total_typing_time = 0

        init_time = False

        lines = f.readlines()

        index = 0
        # Loop over each line
        for line in lines:
            z = re.match(".*?at\s(\w{3}\s\w{3}\s\d{2}\s\d{2}:\d{2}:\d{2}\s2019)]\s(.*?)$", line)
            if not z:
                continue

            groups = z.groups()
            time_pressed = groups[0]
            time_pressed = time.strptime(time_pressed, "%a %b %d %H:%M:%S %Y")
            key_pressed = groups[1]

            if init_time is False:
                init_time = time_pressed

            # Query submission
            if key_pressed == "[ENTER]":
                num_enters = num_enters + 1
                typing_time = timedelta(seconds=(time.mktime(time_pressed) - time.mktime(init_time)))
                total_typing_time = total_typing_time + typing_time.seconds
                init_time = False
                continue

            # Letter
            if len(key_pressed) == 1:
                num_chars = num_chars + 1
                continue

            # Space
            if len(key_pressed) == 0:
                num_chars = num_chars + 1
                continue

            # Error characters
            num_key_errors = num_key_errors + 1

        # End of lines
        WPM = ((num_key_errors + num_chars + num_enters) / 5) / (total_typing_time / 60)
        print("WPM: ", WPM)

        print("Typing time / Query: ", total_typing_time / num_enters)

        return {
            "WPM": WPM,
            "typing_time": total_typing_time,
            "num_error_chars": num_key_errors,
            "num_output_chars": num_chars + num_enters
        }


# Parse arguments
parser = argparse.ArgumentParser()
parser.add_argument('appLog', help='Text file with app logs for one topic and one user')
parser.add_argument('keyLog', help='Text file with key logs for one topic and one user')
parser.add_argument('destination', help='Target file for analysis')
args = parser.parse_args()

# check if app log input is valid
if not os.path.isfile(args.appLog):
    print("Please specify a valid app log file")
    sys.exit(1)

# check if key log input is valid
if not os.path.isfile(args.keyLog):
    print("Please specify a valid key log file")
    sys.exit(1)

# check output is defined
if not args.destination:
    print("Please specify a destination file")
    sys.exit(1)

app_log_results = analyse_app_log(args.appLog)
key_log_results = analyse_keylog(args.keyLog)

with open(args.destination, "w+") as d:
    d.write("Typing Time / Query: " + str(key_log_results["typing_time"] / app_log_results["num_queries"]) + "\n")
    d.write("Assessment Time / Query: " + str((SECONDS_PER_TOPIC - key_log_results["typing_time"])/app_log_results["num_queries"]) + "\n")
    d.write("Total Time / Query: " + str(SECONDS_PER_TOPIC / app_log_results["num_queries"]) + "\n")
    d.write("On-Topic Typing / Query (WPM): " + str(key_log_results["WPM"]) + "\n")
    d.write("Typed Characters / Query: " + str((key_log_results["num_output_chars"] + key_log_results["num_error_chars"]) / app_log_results["num_queries"]) + "\n")
    d.write("Error Characters / Query: " + str(
        key_log_results["num_error_chars"] / app_log_results[
            "num_queries"]) + "\n")
    d.write("Output Characters / Query: " + str(
        key_log_results["num_output_chars"] / app_log_results[
            "num_queries"]) + "\n")
    d.write("Number of Queries: " + str(app_log_results["num_queries"]) + "\n")
    d.write("Documents Marked: " + str(app_log_results["num_marked"]) + "\n")
    d.write("Documents clicked: " + str(app_log_results["num_clicked"]) + "\n")












