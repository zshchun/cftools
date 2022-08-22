from . import problem
from . import ui
from .util import guess_cid
from os import listdir, path, unlink, sep
import time
import subprocess

def compile_code(src_path, run_path):
# TODO support other languages
# TODO support template strings
    print("[+] Compile {}".format(src_path))
    subprocess.run(["g++", "-O2", "-o", run_path, src_path], capture_output=True)

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
    for in_file in input_files:
        d = path.dirname(in_file)
        f = path.basename(in_file)
        output_file = d + sep + 'ans' + f[2:]
        #print(output_file)
        if not path.isfile(output_file):
            continue
        # TODO timeout
        # TODO diff result
        proc = subprocess.Popen([run_path], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        inputs = open(in_file, "rb").read()
        proc.stdin.write(inputs)
        outputs, error = proc.communicate()
        expected_outputs = open(output_file, "rb").read()
        if outputs == expected_outputs:
            ui.green("Accepted")
        else:
            ui.red("Wrong Answer")
    unlink(run_path)

