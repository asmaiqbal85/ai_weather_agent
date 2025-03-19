import subprocess
def run():
    subprocess.run(["chainlit", "run", ".//src//weather//main.py", "-w"])