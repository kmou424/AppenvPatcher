import subprocess


class Cmdline:
    @staticmethod
    def run(cmd: str):
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
