"""What `help` prints.

Generated from the grammar and the role's own table, so it lists what the role
will actually accept. The three roles used to keep their own hand-written
block, which is why they had drifted from the commands they took.
"""

from .grammar import USAGES


def help_text(role):
    """The commands this role accepts, one per line."""
    lines = []
    for usage in USAGES:
        if usage.kind not in role.kinds:
            continue
        if usage.subject is not None and usage.subject not in role.show_subjects:
            continue
        lines.append(f'{usage.usage} - {usage.description}')
    return '\n'.join(lines)


def print_help(role):
    print()
    print(help_text(role))
    print()
