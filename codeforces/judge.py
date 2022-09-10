from . import problem
from .ui import *
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
        print(RED("[!] Compile error!"))
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
    idx = 0
    for in_file in input_files:
        idx += 1
        d = path.dirname(in_file)
        f = path.basename(in_file)
        output_file = d + sep + 'ans' + f[2:]
        if not path.isfile(output_file):
            continue
        start_time = time()
        inputs = open(in_file, "rb").read()
        try:
            proc = subprocess.run([run_path], input=inputs, check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=5)
            outputs = proc.stdout
            end_time = time()
            expected_outputs = open(output_file, "rb").read()
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
                    report += RED(o1.ljust(20, ' '))
                    report += GREEN(o2.ljust(20, ' ')) + '\n'
            if same:
                ac += 1
                print(GREEN("Passed #"+str(idx)), GRAY("... {:.3f}s".format(end_time-start_time)))
            else:
                print(RED("Failed #"+str(idx)), GRAY("... {:.3f}s".format(end_time-start_time)))
                print(WHITE("=======  IN #{:d} =======".format(idx)))
                print(inputs.decode())
                print(WHITE("======= OUT #{:d} =======".format(idx)))
                print(report)
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as err:
            print(RED("Failed #{}".format(idx)))
            if err.stdout: print(e.stdout.decode())
            print(GRAY(str(err)))
    total = len(input_files)
    ac_text = "[{}/{}]".format(ac, total)
    if total == 0:
        print(RED("[!] There is no testcases"))
    elif total == ac:
        print(ac_text, GREEN("Accepted"))
    else:
        print(ac_text, RED("Wrong Answer"))
    unlink(run_path)
