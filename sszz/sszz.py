"""Module with main script for Simple SZZ."""

import logging
import re
from collections import namedtuple

import click
import git
from git import Repo
from gitdb.exc import BadName
from git.exc import GitCommandError

@click.command()
@click.option('--repo', prompt=True, default="./", help="Path to the git repository.")
@click.option('--commit', prompt=True, help="Commit to be analyzed.")
@click.option('--log', help="Specify log level (DEBUG|INFO|WARNING|ERROR|CRITICAL).")
def tool(repo, commit, log):
    """CLI to run SZZ for a commit."""
    if log:
        log_numeric_level = getattr(logging, log.upper())
        logging.basicConfig(level=log_numeric_level)
    click.echo(find_refactoring_commit(repo, commit))

def find_refactoring_commit(repo_dir, commit_sha):
    """Look for a bug fix that blames change induced by this commit."""
    logging.info(
        'Looking for bug fixing commits for '
        f'commit {commit_sha} '
        f'in repo "{repo_dir}".'
    )
    return next(
        (future_commit
         for future_commit in get_all_commits_since(repo_dir, commit_sha)
         if check_refactoring_has_happened(repo_dir, commit_sha, future_commit)),  
        None
    )

def find_refactoring_commit_binary(repo_dir, commit_sha, future_commits=None):
    if future_commits is None:
        future_commits = get_all_commits_since(repo_dir, commit_sha)
    if len(future_commits) == 0:
        return None
    future_commit_index = int((len(future_commits)-1)/2)
    future_commit = future_commits[future_commit_index]
    if check_refactoring_has_happened(repo_dir, commit_sha, future_commit):
        if len(future_commits) == 1:
            return future_commits[0]
        else:
            future_commits = future_commits[:future_commit_index+1]
    else:
        future_commits = future_commits[future_commit_index+1:]
    return find_refactoring_commit_binary(
        repo_dir,
        commit_sha,
        future_commits
    )
def check_refactoring_has_happened(repo_dir, commit_a, commit_b):
    """Check whether, at the moment of commit_b, code from commit_a has been refactored."""
    logging.info(f"Checking whether commit {commit_b} refactors {commit_a}.")
    commit_ap = f"{commit_a}^1"
    commit_bp = f"{commit_b}^1"
    changes_ap_to_a = git_compare_commits(repo_dir, commit_ap, commit_a)
    # changes_ap_to_bp = git_compare_commits(repo_dir, commit_ap, commit_bp)
    changes_ap_to_b = git_compare_commits(repo_dir, commit_ap, commit_b)
    # changes_a_to_bp = git_compare_commits(repo_dir, commit_a, commit_bp)
    changes_a_to_b = git_compare_commits(repo_dir, commit_a, commit_b)
    code_was_refactored_between_a_and_b = ((changes_ap_to_a+changes_a_to_b) != changes_ap_to_b)
    # code_was_refactored_between_a_and_bp = ((changes_ap_to_a+changes_a_to_bp) != changes_ap_to_bp)
    code_was_refactored_by_b = (
        code_was_refactored_between_a_and_b
        # and
        # not(code_was_refactored_between_a_and_bp)
    )
    return code_was_refactored_by_b

def check_refactoring_commit(repo_dir, commit_a, commit_b):
    """Check whether commit_b refactors code from commit_a."""
    logging.info(f"Checking whether commit {commit_b} refactors {commit_a}.")
    commit_ap = f"{commit_a}^1"
    commit_bp = f"{commit_b}^1"
    changes_ap_to_a = git_compare_commits(repo_dir, commit_ap, commit_a)
    changes_ap_to_bp = git_compare_commits(repo_dir, commit_ap, commit_bp)
    changes_ap_to_b = git_compare_commits(repo_dir, commit_ap, commit_b)
    changes_a_to_bp = git_compare_commits(repo_dir, commit_a, commit_bp)
    changes_a_to_b = git_compare_commits(repo_dir, commit_a, commit_b)
    code_was_refactored_between_a_and_b = ((changes_ap_to_a+changes_a_to_b) != changes_ap_to_b)
    code_was_refactored_between_a_and_bp = ((changes_ap_to_a+changes_a_to_bp) != changes_ap_to_bp)
    code_was_refactored_by_b = (
        code_was_refactored_between_a_and_b
        and
        not(code_was_refactored_between_a_and_bp)
    )
    return code_was_refactored_by_b


    
    
class Changes(namedtuple('Changes', ['insertions', 'deletions'])):
    """Class to compare changes between commits."""
    def __add__(self, other):
        return Changes(
            self.insertions+other.insertions,
            self.deletions+other.deletions
        )
    def __sub__(self, other):
        return Changes(
            self.insertions-other.insertions,
            self.deletions-other.deletions
        )

def git_compare_commits(repo_dir, commit_a, commit_b):
    "Get number of files changes, insertions and deletions between two commits."
    git_caller = git.cmd.Git(repo_dir)
    result = git_caller.execute(
        ['git', 'diff', '-w', '--shortstat', commit_a, commit_b]
    )
    # files_changed = _get_numeric_var_from_regex_match("(\d+) files? changed", result)
    insertions = _get_numeric_var_from_regex_match("(\d+) insertions?\(\+\)", result)
    deletions = _get_numeric_var_from_regex_match("(\d+) deletions?\(-\)", result)
    return Changes(insertions, deletions)

def _get_numeric_var_from_regex_match(pattern, string):
    match = re.search(pattern, string)
    if match:
        return int(match.group(1))
    return 0
def _add_tuples(t1, t2):
    return tuple(sum(values) for values in zip(t1, t2))

def get_all_commits_since(repo_dir, commit_sha):
    """Get a list of all commits made after the given commit."""
    #git log --pretty='%H' 10edd33598c80b6e9453bd8c0117b29f004837d3..HEAD
    try:
        git_caller = git.cmd.Git(repo_dir)
        output = git_caller.execute(
            ['git', 'log', "--pretty=%H", f"{commit_sha}..HEAD"]
        )
        return output.split('\n')[::-1]
    except GitCommandError as git_error:
        _, _, error_message, *_ = git_error.args
        if "Invalid revision range" in error_message.decode():
            raise CommitNotFound()
        else:
            raise git_error
        


class SSZZException(Exception):
    """Base Class for SSZZ exceptions."""
    pass

class CommitWithoutParent(SSZZException):
    """Base Class for gitutils exceptions."""
    pass

class CommitNotFound(SSZZException):
    """Exception raised when given commit is not found."""
    pass

if __name__ == '__main__':
    tool() # pylint: disable=no-value-for-parameter

