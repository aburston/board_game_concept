"""The shell completion for launching a role, run in a real shell.

The scripts know two things about where a game is kept - `games/_<gameno>` and
the player files inside it - and the repository is what decides both. These
tests run the completion functions in a shell against a game the repository
actually wrote, so the two cannot drift apart quietly.
"""

import os
import shutil
import subprocess

import pytest

from game_harness import GameHarness

# the shell completion knows the YAML directory layout by name - "players"
# under each game, one YAML file per player, one number per file name. Under
# any other backend the layout is different, and these tests are about the
# YAML one
pytestmark = pytest.mark.backend('yaml')

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASH_COMPLETION = os.path.join(ROOT, 'completions', 'bgc.bash')

ZSH_COMPLETION = os.path.join(ROOT, 'completions', 'bgc.zsh')

BASH = shutil.which('bash')
ZSH = shutil.which('zsh')

needs_bash = pytest.mark.skipif(BASH is None, reason='no bash to run it in')


def in_bash(script, cwd):
    """Run a line of bash with the completion sourced, and split what it printed."""
    result = subprocess.run(
        [BASH, '-c', f'source {BASH_COMPLETION!r}\n{script}'],
        cwd=str(cwd), capture_output=True, text=True, timeout=30, check=True)
    return result.stdout.split()


def completion_for(words, position, function, cwd):
    """What the completion function offers for a command line being typed."""
    quoted = ' '.join(f'"{word}"' for word in words)
    return in_bash(
        f'COMP_WORDS=({quoted})\nCOMP_CWORD={position}\n{function}\n'
        'printf "%s\\n" "${COMPREPLY[@]}"', cwd)


def a_game(tmp_path, gameno='harness', players=(1, 2)):
    harness = GameHarness(tmp_path, gameno)
    harness.create(4, 4, list(players))
    return harness


@needs_bash
def test_the_game_numbers_offered_are_the_games_on_disk(tmp_path):
    a_game(tmp_path, 'one')
    a_game(tmp_path, 'two')

    assert sorted(in_bash('_bgc_game_numbers', tmp_path)) == ['one', 'two']


@needs_bash
def test_the_player_numbers_offered_are_the_ones_the_repository_kept(tmp_path):
    harness = a_game(tmp_path, 'harness', players=(1, 2, 3))

    offered = in_bash('_bgc_player_numbers harness', tmp_path)

    assert sorted(int(number) for number in offered) == sorted(
        harness.repository().player_numbers())


@needs_bash
def test_a_players_other_files_are_not_offered_as_players(tmp_path):
    # a player is `<number>.yaml`; their orders, their view and their
    # rejections live beside it under names that are not a player
    harness = a_game(tmp_path)
    harness.deploy(1, [('tank', 'T', 3, 5, 10)], [('tank', 'alpha', 0, 0)])
    players = tmp_path / 'games' / '_harness' / 'players'

    offered = in_bash('_bgc_player_numbers harness', tmp_path)

    assert [name for name in os.listdir(players) if '_' in name]
    assert sorted(offered) == ['1', '2']


@needs_bash
def test_the_client_completes_a_game_then_a_player(tmp_path):
    a_game(tmp_path, 'harness')

    games = completion_for(['bgcclient', ''], 1, '_bgcclient', tmp_path)
    players = completion_for(['bgcclient', 'harness', ''], 2, '_bgcclient',
                             tmp_path)

    assert games == ['harness']
    assert sorted(players) == ['1', '2']


@needs_bash
def test_the_observer_completes_a_game_number(tmp_path):
    a_game(tmp_path, 'harness')

    assert completion_for(['bgcobserver', ''], 1, '_bgcobserver',
                          tmp_path) == ['harness']


@needs_bash
def test_the_server_completes_a_game_number_after_its_option(tmp_path):
    a_game(tmp_path, 'harness')

    offered = completion_for(['bgcserver', '-g', ''], 2, '_bgcserver', tmp_path)

    assert offered == ['harness']


@needs_bash
def test_the_server_completes_its_options(tmp_path):
    offered = completion_for(['bgcserver', '-'], 1, '_bgcserver', tmp_path)

    assert '-g' in offered and '--game-number' in offered


@needs_bash
def test_a_partly_typed_game_number_narrows_what_is_offered(tmp_path):
    a_game(tmp_path, 'alpha')
    a_game(tmp_path, 'beta')

    offered = completion_for(['bgcclient', 'al'], 1, '_bgcclient', tmp_path)

    assert offered == ['alpha']


@needs_bash
def test_a_directory_with_no_games_offers_nothing(tmp_path):
    assert in_bash('_bgc_game_numbers', tmp_path) == []
    assert in_bash('_bgc_player_numbers harness', tmp_path) == []
    assert completion_for(['bgcclient', ''], 1, '_bgcclient', tmp_path) == []


# The zsh script cannot be run through a completion function without a
# completion context, so what is checked here is what can be: that it covers
# the three commands, that it looks where the repository writes, and - where
# there is a zsh to ask - that zsh reads it as a script.

def test_the_zsh_completion_covers_the_three_commands():
    script = open(ZSH_COMPLETION, encoding='utf-8').read()

    for command in ('bgcclient', 'bgcserver', 'bgcobserver'):
        assert f'compdef _{command} {command}' in script


def test_the_zsh_completion_looks_where_the_repository_writes(tmp_path):
    harness = a_game(tmp_path, 'harness')
    repository = harness.repository()
    script = open(ZSH_COMPLETION, encoding='utf-8').read()

    # the two paths the script globs, written as the repository writes them
    assert os.path.relpath(repository.root, tmp_path) == os.path.join(
        'games', '_harness')
    assert os.path.relpath(repository.player_path, tmp_path) == os.path.join(
        'games', '_harness', 'players')
    assert 'games/_*(N/)' in script
    assert 'games/_${gameno}/players/*.yaml(N)' in script


@pytest.mark.skipif(ZSH is None, reason='no zsh to read it')
def test_zsh_reads_the_completion_as_a_script():
    subprocess.run([ZSH, '-n', ZSH_COMPLETION], check=True, timeout=30,
                   capture_output=True)
