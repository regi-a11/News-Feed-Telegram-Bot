import os
from time import sleep
import datetime

# Function to run the main fetch_and_notify script
def run_task():
    # Update the Python interpreter path and script path as per your environment
    os.system('python3 /Users/reginoldkbinoy/PycharmProjects/Telegram_Bot/fetch_and_notify.py')

# Infinite loop to keep the script running
while True:
    # Run the task
    run_task()

    # Print current time for debugging
    print(f"Task ran at: {datetime.datetime.now()}")

    # Sleep for 30 minutes (1800 seconds)
    sleep(1800)
