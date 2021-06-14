import subprocess
from os import listdir, mkdir, path, rename
from time import sleep
from datetime import datetime
from shutil import rmtree

# последовательно считывает каталоги и выполняет код

def run_code(filepath, input) -> str:
    try:
        start = datetime.now()
        p = subprocess.run(
            ["python3.9", filepath],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            input=input,
            timeout=1, # секунды
            encoding='utf-8',
        )
        duration = datetime.now() - start

        #p.stdout, p.stderr, p.returncode
        return p.stdout
    except Exception as e:
        print('exception!')
        duration = datetime.now() - start
        return None

if __name__ == '__main__':
    while True:
        # работа с каталогами
        dirs = [ x for x in listdir('/test_dir_execute') if x.endswith('+') and path.isdir(path.join('/test_dir_execute', x)) ]
        print(dirs)

        if len(dirs) == 0:
            sleep(1)

        for dir in dirs:
            dir_tests = path.join('/test_dir_execute', dir)
            dir_res = path.join('/test_dir_executed', dir[:-1])

            if path.exists(dir_res):
                rmtree(dir_res)
            mkdir(dir_res)

            filenames = [ x for x in listdir(dir_tests) if x != 'code.py' ]

            code_path = path.join(dir_tests, 'code.py')
            for filename in filenames:
                with open(path.join(dir_tests, filename), 'rt') as fin:
                    input = fin.read()
                
                output = run_code(code_path, input)

                with open(path.join(dir_res, filename), 'wt') as fout:
                    fout.write(output)

            rename(dir_res, dir_res+'+')
            rename(dir_tests, dir_tests[:-1])