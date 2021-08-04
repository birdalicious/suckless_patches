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


# Path to repo to reset
def git_reset_clean(path):
    cwd = os.getcwd()
    os.chdir(path)

    process = subprocess.Popen(["git", "reset", "--hard"], stdout=subprocess.PIPE)
    process.wait()
    process = subprocess.Popen(["git", "clean", "-f"], stdout=subprocess.PIPE)
    process.wait()

    os.chdir(cwd)


# Path to repo to get the short hash of
def git_get_shorthash(path):
    cwd = os.getcwd()
    os.chdir(path)

    process = subprocess.Popen(["git", "rev-parse", "--short", "HEAD"], stdout=subprocess.PIPE)
    process.wait()

    os.chdir(cwd)
    return process.communicate()[0].decode('utf-8')[:-1]


def cloneRepo(path, url):
    cmd = ["git", "clone", url, path]

    if os.path.isfile(path):
        raise ValueError('path should point to a directory')

    if os.path.isdir(path):
        return

    print(f'Downloading {url}')
    process = subprocess.Popen(cmd, stderr=subprocess.PIPE)
    process.wait()
    print('download complete')


def updateRepo(path, master='master'):
    cwd = os.getcwd()
    os.chdir(path)
    print(f'Updating {path}:')
    if not os.path.isdir('.git'):
       print(f'ERROR: {path} not a git repo')
       exit(1)
    process = subprocess.Popen(["git", "pull", "origin", master], stderr=subprocess.PIPE)
    process.wait()

    os.chdir(cwd)
    git_reset_clean(path)


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


def listPatches(tool, sites_path):
    checkTool(tool)
    patch_path = os.path.join(sites_path, PATCH_PATHS[tool])
    return [patch for patch in os.listdir(patch_path) if os.path.isdir(os.path.join(patch_path, patch))]

def listPatchPaths(tool, sites_path):
    checkTool(tool)
    patch_path = os.path.join(sites_path, PATCH_PATHS[tool])
    return [os.path.join(patch_path, patch) for patch in listPatches(tool, sites_path)]

def listDiffPaths(path):
    diffs = []
    for root, dirs, files in os.walk(path, topdown=False):
        for file in files:
            if file.endswith('.diff'):
                diffs.append(os.path.join(root, file))
    return diffs

def listDiffs(path):
    return [os.path.basename(diff) for diff in listDiffPaths(path)]


def countWorking(patchWorksDict):
    c = 0
    for patch in patchWorksDict:
        if patchWorksDict[patch]:
            c += 1
    return c

def countBroken(patchWorksDict):
    return len(patchWorksDict.keys()) - countWorking(patchWorksDict)


def checkTool(tool):
    if tool in TOOLS:
        return tool
    raise ValueError(f'{tool} is not in the tool list: {list(TOOLS)}')

def main():
    parser = argparse.ArgumentParser(description='Checks if patches can be applied')
    parser.add_argument('tool', type=checkTool, help='suckless tool name to check patches on')
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
    

    # Repo management
    cloneRepo(args.tool_path, f'{SUCKLESS}{args.tool}')
    cloneRepo(args.sites_path, f'{SUCKLESS}{SITES}')
    updateRepo(args.tool_path)
    updateRepo(args.sites_path)

    # Set default output file
    SHORTHASH = git_get_shorthash(args.tool_path)
    if not args.output:
        if args.patches != 'all':
            args.output = os.path.join(dname, f'{args.tool}-patches-broken.md')
        else:
            args.output = os.path.join(dname, f'{args.tool}-{SHORTHASH}-broken.md')

    patchWorksDict = {}
    patchList = listPatchPaths(args.tool, args.sites_path) if args.patches == 'all' else [os.path.join(args.sites_path,PATCH_PATHS[args.tool], patch) for patch in args.patches.split(',')]
    # Check patchs can be applied
    for path in patchList:
        patch = os.path.basename(path)
        works = False
        for diff in listDiffPaths(path):
            if diffWorks(diff, args.tool_path):
                works = True
                break
        patchWorksDict[patch] = works
        print(patch, works)
    
    # Output
    with open(args.output, "w") as f:
        for patch in sorted(list(patchWorksDict.keys())):
            if not patchWorksDict[patch]:
                f.writelines(f'{patch}\n')


    print(f'\n{countBroken(patchWorksDict)}/{len(patchWorksDict.keys())} broken patches')

if __name__ == '__main__':
    main()
