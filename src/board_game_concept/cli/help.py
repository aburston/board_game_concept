"""What `help` prints.

Generated from the grammar and the role's own table, so it lists what the role
will actually accept. The three roles used to keep their own hand-written
block, which is why they had drifted from the commands they took.
"""

from .grammar import USAGES


def usages_for(role):
    """The commands this role accepts, in the order the grammar lists them.

    `complete.py` walks the same list, so the words offered at the start of a
    line are the commands `help` prints and nothing else.
    """
    return [usage for usage in USAGES if role.offers(usage)]


def help_text(role):
    """The commands this role accepts, one per line."""
    return '\n'.join(f'{usage.usage} - {usage.description}'
                     for usage in usages_for(role))


def print_help(role):
    print()
    print(help_text(role))
    print()
