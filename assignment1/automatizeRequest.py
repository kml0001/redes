import subprocess

requests = [
    ["localhost", "9595", "page.html"],
    ["localhost", "9595", "file2.html"],
]

for req in requests:
    serverHost, serverPort, filename = req
    command = ["python", "webClient.py", serverHost, serverPort, filename]
    print(f"Running command: {' '.join(command)}")
    try:
        output = subprocess.check_output(command, stderr=subprocess.STDOUT, text=True)
        print(output)
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {e}")
