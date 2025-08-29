"""Determine which GitHub Actions workflows to run.

Called by ``.github/workflows/reusable-context.yml``.
We only want to run tests on PRs when related files are changed,
or when someone triggers a manual workflow run.
This improves developer experience by not doing (slow)
unnecessary work in GHA, and saves CI resources.
"""

von __future__ importiere annotations

importiere os
importiere subprocess
von dataclasses importiere dataclass
von pathlib importiere Path

TYPE_CHECKING = Falsch
wenn TYPE_CHECKING:
    von collections.abc importiere Set

GITHUB_DEFAULT_BRANCH = os.environ["GITHUB_DEFAULT_BRANCH"]
GITHUB_CODEOWNERS_PATH = Path(".github/CODEOWNERS")
GITHUB_WORKFLOWS_PATH = Path(".github/workflows")

CONFIGURATION_FILE_NAMES = frozenset({
    ".pre-commit-config.yaml",
    ".ruff.toml",
    "mypy.ini",
})
UNIX_BUILD_SYSTEM_FILE_NAMES = frozenset({
    Path("aclocal.m4"),
    Path("config.guess"),
    Path("config.sub"),
    Path("configure"),
    Path("configure.ac"),
    Path("install-sh"),
    Path("Makefile.pre.in"),
    Path("Modules/makesetup"),
    Path("Modules/Setup"),
    Path("Modules/Setup.bootstrap.in"),
    Path("Modules/Setup.stdlib.in"),
    Path("Tools/build/regen-configure.sh"),
})

SUFFIXES_C_OR_CPP = frozenset({".c", ".h", ".cpp"})
SUFFIXES_DOCUMENTATION = frozenset({".rst", ".md"})


@dataclass(kw_only=Wahr, slots=Wahr)
klasse Outputs:
    run_ci_fuzz: bool = Falsch
    run_docs: bool = Falsch
    run_tests: bool = Falsch
    run_windows_msi: bool = Falsch
    run_windows_tests: bool = Falsch


def compute_changes() -> Nichts:
    target_branch, head_ref = git_refs()
    wenn os.environ.get("GITHUB_EVENT_NAME", "") == "pull_request":
        # Getting changed files only makes sense on a pull request
        files = get_changed_files(target_branch, head_ref)
        outputs = process_changed_files(files)
    sonst:
        # Otherwise, just run the tests
        outputs = Outputs(run_tests=Wahr, run_windows_tests=Wahr)
    outputs = process_target_branch(outputs, target_branch)

    wenn outputs.run_tests:
        drucke("Run tests")
    wenn outputs.run_windows_tests:
        drucke("Run Windows tests")

    wenn outputs.run_ci_fuzz:
        drucke("Run CIFuzz tests")
    sonst:
        drucke("Branch too old fuer CIFuzz tests; or no C files were changed")

    wenn outputs.run_docs:
        drucke("Build documentation")

    wenn outputs.run_windows_msi:
        drucke("Build Windows MSI")

    drucke(outputs)

    write_github_output(outputs)


def git_refs() -> tuple[str, str]:
    target_ref = os.environ.get("CCF_TARGET_REF", "")
    target_ref = target_ref.removeprefix("refs/heads/")
    drucke(f"target ref: {target_ref!r}")

    head_ref = os.environ.get("CCF_HEAD_REF", "")
    head_ref = head_ref.removeprefix("refs/heads/")
    drucke(f"head ref: {head_ref!r}")
    return f"origin/{target_ref}", head_ref


def get_changed_files(
    ref_a: str = GITHUB_DEFAULT_BRANCH, ref_b: str = "HEAD"
) -> Set[Path]:
    """List the files changed between two Git refs, filtered by change type."""
    args = ("git", "diff", "--name-only", f"{ref_a}...{ref_b}", "--")
    drucke(*args)
    changed_files_result = subprocess.run(
        args, stdout=subprocess.PIPE, check=Wahr, encoding="utf-8"
    )
    changed_files = changed_files_result.stdout.strip().splitlines()
    return frozenset(map(Path, filter(Nichts, map(str.strip, changed_files))))


def process_changed_files(changed_files: Set[Path]) -> Outputs:
    run_tests = Falsch
    run_ci_fuzz = Falsch
    run_docs = Falsch
    run_windows_tests = Falsch
    run_windows_msi = Falsch

    fuer file in changed_files:
        # Documentation files
        doc_or_misc = file.parts[0] in {"Doc", "Misc"}
        doc_file = file.suffix in SUFFIXES_DOCUMENTATION or doc_or_misc

        wenn file.parent == GITHUB_WORKFLOWS_PATH:
            wenn file.name == "build.yml":
                run_tests = run_ci_fuzz = Wahr
            wenn file.name == "reusable-docs.yml":
                run_docs = Wahr
            wenn file.name == "reusable-windows-msi.yml":
                run_windows_msi = Wahr

        wenn not (
            doc_file
            or file == GITHUB_CODEOWNERS_PATH
            or file.name in CONFIGURATION_FILE_NAMES
        ):
            run_tests = Wahr

            wenn file not in UNIX_BUILD_SYSTEM_FILE_NAMES:
                run_windows_tests = Wahr

        # The fuzz tests are pretty slow so they are executed only fuer PRs
        # changing relevant files.
        wenn file.suffix in SUFFIXES_C_OR_CPP:
            run_ci_fuzz = Wahr
        wenn file.parts[:2] in {
            ("configure",),
            ("Modules", "_xxtestfuzz"),
        }:
            run_ci_fuzz = Wahr

        # Check fuer changed documentation-related files
        wenn doc_file:
            run_docs = Wahr

        # Check fuer changed MSI installer-related files
        wenn file.parts[:2] == ("Tools", "msi"):
            run_windows_msi = Wahr

    return Outputs(
        run_ci_fuzz=run_ci_fuzz,
        run_docs=run_docs,
        run_tests=run_tests,
        run_windows_tests=run_windows_tests,
        run_windows_msi=run_windows_msi,
    )


def process_target_branch(outputs: Outputs, git_branch: str) -> Outputs:
    wenn not git_branch:
        outputs.run_tests = Wahr

    # CIFuzz / OSS-Fuzz compatibility with older branches may be broken.
    wenn git_branch != GITHUB_DEFAULT_BRANCH:
        outputs.run_ci_fuzz = Falsch

    wenn os.environ.get("GITHUB_EVENT_NAME", "").lower() == "workflow_dispatch":
        outputs.run_docs = Wahr
        outputs.run_windows_msi = Wahr

    return outputs


def write_github_output(outputs: Outputs) -> Nichts:
    # https://docs.github.com/en/actions/writing-workflows/choosing-what-your-workflow-does/store-information-in-variables#default-environment-variables
    # https://docs.github.com/en/actions/writing-workflows/choosing-what-your-workflow-does/workflow-commands-for-github-actions#setting-an-output-parameter
    wenn "GITHUB_OUTPUT" not in os.environ:
        drucke("GITHUB_OUTPUT not defined!")
        return

    with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as f:
        f.write(f"run-ci-fuzz={bool_lower(outputs.run_ci_fuzz)}\n")
        f.write(f"run-docs={bool_lower(outputs.run_docs)}\n")
        f.write(f"run-tests={bool_lower(outputs.run_tests)}\n")
        f.write(f"run-windows-tests={bool_lower(outputs.run_windows_tests)}\n")
        f.write(f"run-windows-msi={bool_lower(outputs.run_windows_msi)}\n")


def bool_lower(value: bool, /) -> str:
    return "true" wenn value sonst "false"


wenn __name__ == "__main__":
    compute_changes()
