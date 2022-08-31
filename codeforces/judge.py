from . import problem
from . import ui
from .util import guess_cid
from os import listdir, path, unlink, sep
from sys import exit
from time import time
import subprocess

def compile_code(src_path, run_path):
# TODO support other languages
# TODO support template strings
# TODO memory usage
    print("[+] Compile {}".format(src_path))
    proc = subprocess.run(["g++", "-O2", "-o", run_path, src_path], capture_output=True)
    if proc.returncode != 0:
        if proc.stdout:
            print(proc.stdout.decode())
        if proc.stderr:
            print(proc.stderr.decode())
        ui.red("[!] Compile error!")
        exit(1)

def test(args):
    cid, level = guess_cid(args)
    if not cid or not level:
        print("[!] Invalid contestID or level")
        return
    prob_dir = problem.prepare_problem_dir(cid, level)

    if args.input:
        filename = args.input
    else:
        filename = problem.select_source_code(cid, level)
    if not path.isfile(filename):
        print("[!] File not found : {}".format(filename))
        return
    run_path = path.splitext(filename)[0]
    input_files = problem.find_input_files(prob_dir)
    compile_code(filename, run_path)
    ac = 0
    idx = 1
    for in_file in input_files:
        d = path.dirname(in_file)
        f = path.basename(in_file)
        output_file = d + sep + 'ans' + f[2:]
        if not path.isfile(output_file):
            continue
        start_time = time()
        proc = subprocess.Popen([run_path], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        inputs = open(in_file, "rb").read()
        proc.stdin.write(inputs)
        try:
            outputs, error = proc.communicate(timeout=5)
            end_time = time()
            expected_outputs = open(output_file, "rb").read()
            if proc.returncode != 0:
                print("[!] Failed with exit code : {}".format(proc.returncode))
                if outputs: print(outputs.decode())
                if error: print(error.decode())
                continue
            same = True
            report = ''
            a = outputs.decode().splitlines()
            b = expected_outputs.decode().splitlines()
            max_length = max(len(a), len(b))
            a += [''] * (max_length - len(a))
            b += [''] * (max_length - len(b))
            for o1, o2 in zip(a, b):
                if o1.strip() == o2.strip():
                    report += o1.ljust(20, ' ') * 2 + '\n'
                    continue
                else:
                    same = False
                    report += ui.setcolor('red', o1.ljust(20, ' '))
                    report += ui.setcolor('green', o2.ljust(20, ' ')) + '\n'
            if same:
                ac += 1
                print(ui.setcolor("green", "Passed #"+str(idx)), ui.setcolor("gray", "... {:.3f}s".format(end_time-start_time)))
            else:
                print(ui.setcolor("red", "Failed #"+str(idx)), ui.setcolor("gray", "... {:.3f}s".format(end_time-start_time)))
                ui.white("=======  IN #{:d} =======".format(idx))
                print(inputs.decode())
                ui.white("======= OUT #{:d} =======".format(idx))
                print(report)
        except subprocess.TimeoutExpired:
            proc.kill()
            outputs, error = proc.communicate()
            ui.red("[!] Timeout!")
            if outputs:
                print(outputs.decode())
            if error:
                print(error.decode())
        idx += 1
    total = len(input_files)
    if total == 0:
        ui.red("[!] There is no testcases")
    elif total == ac:
        ui.green("[{}/{}] Accepted".format(ac, total))
    else:
        ui.red("[{}/{}] Wrong Answer".format(ac, total))
    unlink(run_path)
