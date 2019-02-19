from subprocess import Popen, PIPE
import os


def git_describe():

    if not os.path.isdir('.git'):
        raise ValueError('.git not found. Be sure to be inside the git repository.')

    try:
        p = Popen(['git', 'describe', '--tags', '--dirty', '--always'], stdout=PIPE)
    except EnvironmentError:
        print('ERROR: unable to run git. Are you sure it is installed?')
        raise

    git_describe_stdout = p.communicate()[0].decode().strip()
    return git_describe_stdout
