#!/bin/python
import os
import subprocess
import argparse
import re
from shutil import copyfile

SUCKLESS = "git://git.suckless.org/"
SITES = "sites"
PATCH_PATHS = {
    "dwm"   :   "dwm.suckless.org/patches",
    "st"    :   "st.suckless.org/patches",
    "surf"  :   "surf.suckless.org/patches",
    "dmenu" :   "tools.suckless.org/dmenu/patches",
    "ii"    :   "tools.suckless.org/ii/patches",
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

def git_get_tag(path):
    cwd = os.getcwd()
    os.chdir(path)
    process = subprocess.Popen(["git", "describe", "--tags"], stdout=subprocess.PIPE)
    process.wait()
    descriptor = process.communicate()[0].decode('utf-8')[:-1]

    os.chdir(cwd)

    # If the current commit is the one with the tag return the tag otherwise none
    if not re.fullmatch(r'(.+)-[0-9]+-[a-z0-9]+', descriptor):
        return descriptor
    return None

# Path to repo runs the command 'git checkout {value}'
def git_checkout(path, value):
    cwd = os.getcwd()
    os.chdir(path)

    process = subprocess.Popen(["git", "checkout", value], stdout=subprocess.PIPE)
    process.wait()

    os.chdir(cwd)


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
    parser.add_argument('--diff', const=True, action='store_const', dest='diff', help='check and list if every diff file for each patch works')
    parser.add_argument('-o', '--output', metavar='file', dest='output')
    parser.add_argument('--tool', dest='tool_path', metavar='path', help='specify the location of the tool repo')
    parser.add_argument('--commit', dest='commit', metavar='short_hash', default='master', help='specify the commit/tag of the tool to check the patches on')
    parser.add_argument('--sites', dest='sites_path', metavar='path', help='specify the location of the sites repo')

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
    git_checkout(args.tool_path, args.commit)

    # Set default output file
    SHORTHASH = git_get_shorthash(args.tool_path)
    descriptor = git_get_tag(args.tool_path)
    descriptor = descriptor if descriptor else SHORTHASH
    if not args.output:
        file = f'{args.tool}-{descriptor}'
        file += '-patches' if args.patches != 'all' else ''
        file += '-broken.md'

        args.output = os.path.join(dname, file)

    patchWorksDict = {}
    patchList = listPatchPaths(args.tool, args.sites_path) if args.patches == 'all' else [os.path.join(args.sites_path,PATCH_PATHS[args.tool], patch) for patch in args.patches.split(',')]
    output = []

    # Check patchs can be applied
    for path in patchList:
        patch = os.path.basename(path)
        works = False

        print(patch)
        output.append(patch)
        for diff in listDiffPaths(path):
            diffWorking = diffWorks(diff, args.tool_path)
            works = True if diffWorking else works
            if args.diff:
                s = f'\t{os.path.basename(diff)} {diffWorking}'
                print(s)
                output.append(s)
            elif works:
                break
        patchWorksDict[patch] = works
        if works and not args.diff:
            output.pop()

    
    # Output
    with open(args.output, "w") as f:
        for line in output:
            f.writelines(f'{line}\n')


    print(f'\n{countBroken(patchWorksDict)}/{len(patchWorksDict.keys())} broken patches')

if __name__ == '__main__':
    main()