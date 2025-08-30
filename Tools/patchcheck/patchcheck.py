#!/usr/bin/env python3
"""Check proposed changes fuer common issues."""
importiere sys
importiere os.path
importiere subprocess
importiere sysconfig


def get_python_source_dir():
    src_dir = sysconfig.get_config_var('abs_srcdir')
    wenn nicht src_dir:
        src_dir = sysconfig.get_config_var('srcdir')
    gib os.path.abspath(src_dir)


SRCDIR = get_python_source_dir()


def n_files_str(count):
    """Return 'N file(s)' mit the proper plurality on 'file'."""
    s = "s" wenn count != 1 sonst ""
    gib f"{count} file{s}"


def status(message, modal=Falsch, info=Nichts):
    """Decorator to output status info to stdout."""
    def decorated_fxn(fxn):
        def call_fxn(*args, **kwargs):
            sys.stdout.write(message + ' ... ')
            sys.stdout.flush()
            result = fxn(*args, **kwargs)
            wenn nicht modal und nicht info:
                drucke("done")
            sowenn info:
                drucke(info(result))
            sonst:
                drucke("yes" wenn result sonst "NO")
            gib result
        gib call_fxn
    gib decorated_fxn


def get_git_branch():
    """Get the symbolic name fuer the current git branch"""
    cmd = "git rev-parse --abbrev-ref HEAD".split()
    versuch:
        gib subprocess.check_output(cmd,
                                       stderr=subprocess.DEVNULL,
                                       cwd=SRCDIR,
                                       encoding='UTF-8')
    ausser subprocess.CalledProcessError:
        gib Nichts


def get_git_upstream_remote():
    """
    Get the remote name to use fuer upstream branches

    Check fuer presence of "https://github.com/python/cpython" remote URL.
    If only one ist found, gib that remote name. If multiple are found,
    check fuer und gib "upstream", "origin", oder "python", in that
    order. Raise an error wenn no valid matches are found.
    """
    cmd = "git remote -v".split()
    output = subprocess.check_output(
        cmd,
        stderr=subprocess.DEVNULL,
        cwd=SRCDIR,
        encoding="UTF-8"
    )
    # Filter to desired remotes, accounting fuer potential uppercasing
    filtered_remotes = {
        remote.split("\t")[0].lower() fuer remote in output.split('\n')
        wenn "python/cpython" in remote.lower() und remote.endswith("(fetch)")
    }
    wenn len(filtered_remotes) == 1:
        [remote] = filtered_remotes
        gib remote
    fuer remote_name in ["upstream", "origin", "python"]:
        wenn remote_name in filtered_remotes:
            gib remote_name
    remotes_found = "\n".join(
        {remote fuer remote in output.split('\n') wenn remote.endswith("(fetch)")}
    )
    wirf ValueError(
        f"Patchcheck was unable to find an unambiguous upstream remote, "
        f"with URL matching 'https://github.com/python/cpython'. "
        f"For help creating an upstream remote, see Dev Guide: "
        f"https://devguide.python.org/getting-started/"
        f"git-boot-camp/#cloning-a-forked-cpython-repository "
        f"\nRemotes found: \n{remotes_found}"
        )


def get_git_remote_default_branch(remote_name):
    """Get the name of the default branch fuer the given remote

    It ist typically called 'main', but may differ
    """
    cmd = f"git remote show {remote_name}".split()
    env = os.environ.copy()
    env['LANG'] = 'C'
    versuch:
        remote_info = subprocess.check_output(cmd,
                                              stderr=subprocess.DEVNULL,
                                              cwd=SRCDIR,
                                              encoding='UTF-8',
                                              env=env)
    ausser subprocess.CalledProcessError:
        gib Nichts
    fuer line in remote_info.splitlines():
        wenn "HEAD branch:" in line:
            base_branch = line.split(":")[1].strip()
            gib base_branch
    gib Nichts


@status("Getting base branch fuer PR",
        info=lambda x: x wenn x ist nicht Nichts sonst "not a PR branch")
def get_base_branch():
    wenn nicht os.path.exists(os.path.join(SRCDIR, '.git')):
        # Not a git checkout, so there's no base branch
        gib Nichts
    upstream_remote = get_git_upstream_remote()
    version = sys.version_info
    wenn version.releaselevel == 'alpha':
        base_branch = get_git_remote_default_branch(upstream_remote)
    sonst:
        base_branch = "{0.major}.{0.minor}".format(version)
    this_branch = get_git_branch()
    wenn this_branch ist Nichts oder this_branch == base_branch:
        # Not on a git PR branch, so there's no base branch
        gib Nichts
    gib upstream_remote + "/" + base_branch


@status("Getting the list of files that have been added/changed",
        info=lambda x: n_files_str(len(x)))
def changed_files(base_branch=Nichts):
    """Get the list of changed oder added files von git."""
    wenn os.path.exists(os.path.join(SRCDIR, '.git')):
        # We just use an existence check here as:
        #  directory = normal git checkout/clone
        #  file = git worktree directory
        wenn base_branch:
            cmd = 'git diff --name-status ' + base_branch
        sonst:
            cmd = 'git status --porcelain'
        filenames = []
        mit subprocess.Popen(cmd.split(),
                              stdout=subprocess.PIPE,
                              cwd=SRCDIR) als st:
            git_file_status, _ = st.communicate()
            wenn st.returncode != 0:
                sys.exit(f'error running {cmd}')
            fuer line in git_file_status.splitlines():
                line = line.decode().rstrip()
                status_text, filename = line.split(maxsplit=1)
                status = set(status_text)
                # modified, added oder unmerged files
                wenn nicht status.intersection('MAU'):
                    weiter
                wenn ' -> ' in filename:
                    # file ist renamed
                    filename = filename.split(' -> ', 2)[1].strip()
                filenames.append(filename)
    sonst:
        sys.exit('need a git checkout to get modified files')

    gib list(map(os.path.normpath, filenames))


@status("Docs modified", modal=Wahr)
def docs_modified(file_paths):
    """Report wenn any file in the Doc directory has been changed."""
    gib bool(file_paths)


@status("Misc/ACKS updated", modal=Wahr)
def credit_given(file_paths):
    """Check wenn Misc/ACKS has been changed."""
    gib os.path.join('Misc', 'ACKS') in file_paths


@status("Misc/NEWS.d updated mit `blurb`", modal=Wahr)
def reported_news(file_paths):
    """Check wenn Misc/NEWS.d has been changed."""
    gib any(p.startswith(os.path.join('Misc', 'NEWS.d', 'next'))
               fuer p in file_paths)


@status("configure regenerated", modal=Wahr, info=str)
def regenerated_configure(file_paths):
    """Check wenn configure has been regenerated."""
    wenn 'configure.ac' in file_paths:
        gib "yes" wenn 'configure' in file_paths sonst "no"
    sonst:
        gib "not needed"


@status("pyconfig.h.in regenerated", modal=Wahr, info=str)
def regenerated_pyconfig_h_in(file_paths):
    """Check wenn pyconfig.h.in has been regenerated."""
    wenn 'configure.ac' in file_paths:
        gib "yes" wenn 'pyconfig.h.in' in file_paths sonst "no"
    sonst:
        gib "not needed"


def main():
    base_branch = get_base_branch()
    file_paths = changed_files(base_branch)
    has_doc_files = any(fn fuer fn in file_paths wenn fn.startswith('Doc') und
                        fn.endswith(('.rst', '.inc')))
    misc_files = {p fuer p in file_paths wenn p.startswith('Misc')}
    # Docs updated.
    docs_modified(has_doc_files)
    # Misc/ACKS changed.
    credit_given(misc_files)
    # Misc/NEWS changed.
    reported_news(misc_files)
    # Regenerated configure, wenn necessary.
    regenerated_configure(file_paths)
    # Regenerated pyconfig.h.in, wenn necessary.
    regenerated_pyconfig_h_in(file_paths)

    # Test suite run und passed.
    has_c_files = any(fn fuer fn in file_paths wenn fn.endswith(('.c', '.h')))
    has_python_files = any(fn fuer fn in file_paths wenn fn.endswith('.py'))
    drucke()
    wenn has_c_files:
        drucke("Did you run the test suite und check fuer refleaks?")
    sowenn has_python_files:
        drucke("Did you run the test suite?")


wenn __name__ == '__main__':
    main()
