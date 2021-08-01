import os
import subprocess
from shutil import copyfile

SUCKLESS = "git://git.suckless.org/"
SITES = "sites"
PATCH_PATHS = {
    "dwm"   :   "dwm.suckless.org/patches",
    "st"    :   "st.suckless.org/patches",
    "dmenu" :   "tools.suckless.org/dmenu/patches"
}
TOOLS = PATCH_PATHS.keys()

abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)

def git_reset_clean(path):
    cwd = os.getcwd()
    os.chdir(path)

    process = subprocess.Popen(["git", "reset", "--hard"], stdout=subprocess.PIPE)
    process.wait()
    process = subprocess.Popen(["git", "clean", "-f"], stdout=subprocess.PIPE)
    process.wait()

    os.chdir(cwd)


def refreshRepo(path, tool, master='master'):
    if tool not in TOOLS and tool != SITES:
        raise ValueError(f'{tool} is not in the tool list: {TOOLS}')

    cwd = os.getcwd()
    os.chdir(path)

    # Make sure the repo is downloaded
    if not os.path.isdir(tool):
        url = f'{SUCKLESS}{tool}'
        print(f'Downloading {url}')
        process = subprocess.Popen(["git", "clone", f"{url}"], stderr=subprocess.PIPE)
        process.wait()
        print('download complete')

    # Update repo
    os.chdir(tool)
    print(f'Updating {tool}:')
    if not os.path.isdir('.git'):
       print(f'ERROR: {os.path.join(path, tool)} not a git repo')
       exit(1)
    process = subprocess.Popen(["git", "pull", "origin", master], stderr=subprocess.PIPE)
    process.wait()

    os.chdir(cwd)
    git_reset_clean(os.path.join(path, tool))


def diffWorks(patch_path, tool_path):
    cwd = os.getcwd()
    patch_path = os.path.abspath(patch_path)

    os.chdir(tool_path)
    copyfile(patch_path, './patch.diff')

    process = subprocess.Popen(["git", "apply", "patch.diff"], stderr=subprocess.PIPE)
    process.wait()
    output = process.communicate()[1]

    os.chdir(cwd)
    git_reset_clean(tool_path)

    if output == b'':
        return True
    return False
