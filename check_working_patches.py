import os
import subprocess
import argparse
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


def listPatchDirs(tool, sites_path):
    patch_path = os.path.join(sites_path, PATCH_PATHS[tool])
    return os.listdir(patch_path)


def listDiffs(path):
    diffs = []
    for root, dirs, files in os.walk(path, topdown=False):
        for file in files:
            if file.endswith('.diff'):
                diffs.append(os.path.join(root, file))
    return diffs


def main():
    parser = argparse.ArgumentParser(description='Checks if patches can be applied')
    parser.add_argument('tool', help='suckless tool name to check patches on')
    parser.add_argument('-p', '--patches', metavar='patch_name', default='all', dest='patches', help='list of patches to check seperated by a comma, defaults "all"')
    parser.add_argument('-o', '--output', metavar='file', dest='output')
    parser.add_argument('--tool', dest='tool_path', help='specify the location of the tool repo')
    parser.add_argument('--sites', dest='sites_path', help='specify the location of the sites repo')

    args = parser.parse_args()

    #defaults for paths
    if not args.tool_path:
        args.tool_path = os.path.join(dname, args.tool)
    if not args.sites_path:
        args.sites_path = os.path.join(dname, SITES)


    print(args.tool, args.tool_path)


    #TODO
    # Split refresh repo in to clone and update
    # Clone first checks if the folder already exists, if not start the clone
    # then update as normal
    # this will allow for the tool and site path to be set by the user

    refreshRepo(dname, args.tool)
    refreshRepo(dname, SITES)


if __name__ == '__main__':
    main()