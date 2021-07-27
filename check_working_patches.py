import os
import subprocess
from shutil import copyfile

SUCKLESS = "git://git.suckless.org/"
SITES = "sites"
DWM = "dwm"

abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
patchesDir = f'{dname}{SITES}/dwm.suckless.org/patches/'

def git_reset_clean(path):
    cwd = os.getcwd()
    os.chdir(path)

    process = subprocess.Popen(["git", "reset", "--hard"], stdout=subprocess.PIPE)
    process.wait()
    process = subprocess.Popen(["git", "clean", "-f"], stdout=subprocess.PIPE)
    process.wait()

    os.chdir(cwd)


def updateRepos(path):
    cwd = os.getcwd()
    os.chdir(path)

    # Make sure the repos are downloaded
    if not os.path.isdir(SITES):
        print(f'Downloading {SUCKLESS}{SITES}')
        process = subprocess.Popen(["git", "clone", f"{SUCKLESS}{SITES}"], stderr=subprocess.PIPE)
        process.wait()
        print('download complete')
    if not os.path.isdir(DWM):
        print(f'Downloading {SUCKLESS}{DWM}')
        process = subprocess.Popen(["git", "clone", f"{SUCKLESS}{DWM}"], stderr=subprocess.PIPE)
        process.wait()
        print('download complete')

    # update repos
    os.chdir(DWM)
    print(f'{DWM}:')
    process = subprocess.Popen(["git", "pull", "origin", "master"], stderr=subprocess.PIPE)
    process.wait()
    os.chdir(f'../{SITES}')
    print(f'{SITES}:')
    process = subprocess.Popen(["git", "pull", "origin", "master"], stderr=subprocess.PIPE)
    process.wait()

    os.chdir(cwd)
    git_reset_clean(os.path.join(path, DWM))


def diffWorks(patch_path, dwm_path):
    cwd = os.getcwd()
    patch_path = os.path.abspath(patch_path)

    os.chdir(dwm_path)
    copyfile(patch_path, './dwm-patch.diff')

    process = subprocess.Popen(["git", "apply", "dwm-patch.diff"], stderr=subprocess.PIPE)
    process.wait()
    output = process.communicate()[1]

    os.chdir(cwd)
    git_reset_clean(dwm_path)

    if output == b'':
        return True
    return False


updateRepos('./')
print(diffWorks('./sites/dwm.suckless.org/patches/notitle/dwm-notitle-6.2.diff', './dwm'))
