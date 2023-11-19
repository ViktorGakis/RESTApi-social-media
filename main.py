import os
import re
import subprocess

from fastapi import FastAPI

from RESTApi import create_app


def get_os():
    # Fetch the name of the operating system
    platform = os.name

    # Check the platform and print the relevant message
    if platform == "nt":
        return "Windows"
    elif platform == "posix":
        return "Linux or macOS"
    else:
        return "Unknown"


def get_wsl_ip() -> str:
    """
    Fetch the current external IP address of the WSL2 instance using the same approach as the bash shell.
    """
    # Run the 'ip addr show' command and get the output
    result = subprocess.run(
        ["ip", "addr", "show", "eth0"],
        stdout=subprocess.PIPE,
        text=True,
    )

    # Extract the IP address from the command's output
    ip_output = result.stdout
    ip_regex = r"(?<=inet\s)\d+(\.\d+){3}"  # The regex to extract the IP address
    if match := re.search(ip_regex, ip_output):
        return match.group()
    else:
        raise Exception("Could not determine the WSL2 IP address")


app: FastAPI = create_app()

if __name__ == "__main__":
    from uvicorn import run

    PORT = 3000

    if get_os() == "Linux or macOS":
        print("-------- RUNNING ON LINUX ----------")
        # Get the WSL2 IP address
        wsl_ip = get_wsl_ip()

        # Construct the URL that will be used to access the app from the local network
        access_url = f"http://{wsl_ip}:{PORT}"

        print(f"\n\n*-*-* Access the application at: {access_url} *-*-*\n\n")

    # app must have type FastAPI declated otherwise
    # run does not recognise it
    # also need to run sudo service nginx start
    # which is already configured at 3000
    run("main:app", host="0.0.0.0", reload=True, port=PORT)
