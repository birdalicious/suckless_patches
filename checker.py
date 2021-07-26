import os
import subprocess
from shutil import copyfile

abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

# check sites and dwm are downloaded and up to date
if not os.path.isdir('sites'):
    print('Downloading sites')
    process = subprocess.Popen(["git", "clone", "git://git.suckless.org/sites"], stderr=subprocess.PIPE)
    process.wait()
    print('download complete')
if not os.path.isdir('dwm'):
    print('Downloading dwm')
    process = subprocess.Popen(["git", "clone", "git://git.suckless.org/dwm"], stderr=subprocess.PIPE)
    process.wait()
    print('download complete')
# update
print('Checking for updates')
print('dwm:')
os.chdir('./dwm')
process = subprocess.Popen(["git", "pull", "origin", "master"], stderr=subprocess.PIPE)
process.wait()
os.chdir('../sites')
print('sites:')
process = subprocess.Popen(["git", "pull", "origin", "master"], stderr=subprocess.PIPE)
process.wait()
os.chdir('../')

print('Checking patches')

os.chdir('./dwm')

# get short hash for dwm
process = subprocess.Popen(["git", "rev-parse", "--short", "HEAD"], stdout=subprocess.PIPE)
process.wait()
SHORTHASH = process.communicate()[0].decode('utf-8')[:-1]
print(SHORTHASH)


checkedPatches = {}

def patchWorks(patch_path):
    copyfile(patch_path, './dwm-patch.diff')

    process = subprocess.Popen(["git", "apply", "dwm-patch.diff"], stderr=subprocess.PIPE)
    process.wait()
    output = process.communicate()[1]

    process = subprocess.Popen(["git", "reset", "--hard"], stdout=subprocess.PIPE)
    process.wait()
    process = subprocess.Popen(["git", "clean", "-f"], stdout=subprocess.PIPE)
    process.wait()
    if output == b'':
        return True
    return False

# print(patchWorks('notitle/dwm-notitle-20210715-138b405.diff'))



for root, dirs, files in os.walk("../sites/dwm.suckless.org/patches/", topdown=False):
    for diff in files:
        if diff.endswith('.diff'):
            patch_name = os.path.split(root)[-1]
            if patch_name not in checkedPatches.keys():
                checkedPatches[patch_name] = {}
            
            patch_works = patchWorks(os.path.join(root, diff))
            checkedPatches[patch_name][diff] = patch_works
            print(f'Checked {diff}')

print('\n\nChecked All\n\n')
os.chdir('../')

with open(f"{SHORTHASH}-broken.md", "w") as f:
    keys = list(checkedPatches.keys())
    keys.sort()
    for key in keys:
        working = False
        for diff in checkedPatches[key].keys():
            if checkedPatches[key][diff]:
                working = True
                break
        if working == False:
            f.writelines(f'{key}\n')
        
        print(key, f'working: {working}')
