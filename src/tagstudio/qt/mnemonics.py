# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMenu


def remove_mnemonic_marker(label: str) -> str:
    """Remove existing accelerator markers (&) from a label."""
    return label.replace("&&", "<ESC_AMP>").replace("&", "", 1).replace("<ESC_AMP>", "&&")


# Additional weight for first character in string
FIRST_CHARACTER_EXTRA_WEIGHT = 50
# Additional weight for the beginning of a word
WORD_BEGINNING_EXTRA_WEIGHT = 50
# Additional weight for a 'wanted' accelerator ie string with '&'
WANTED_ACCEL_EXTRA_WEIGHT = 150


def calculate_weights(text: str):
    weights: dict[int, str] = {}

    pos = 0
    start_character = True
    wanted_character = False

    while pos < len(text):
        c = text[pos]

        # skip non typeable characters
        if not c.isalnum() and c != "&":
            start_character = True
            pos += 1
            continue

        weight = 1

        # add special weight to first character
        if pos == 0:
            weight += FIRST_CHARACTER_EXTRA_WEIGHT
        elif start_character:  # add weight to word beginnings
            weight += WORD_BEGINNING_EXTRA_WEIGHT
            start_character = False

        # add weight to characters that have an & beforehand
        if wanted_character:
            weight += WANTED_ACCEL_EXTRA_WEIGHT
            wanted_character = False

        # add decreasing weight to left characters
        if pos < 50:
            weight += 50 - pos

        # try to preserve the wanted accelerators
        if c == "&" and (pos != len(text) - 1 and text[pos + 1] != "&" and text[pos + 1].isalnum()):
            wanted_character = True
            pos += 1
            continue

        while weight in weights:
            weight += 1

        if c != "&":
            weights[weight] = c

        pos += 1

    # update our maximum weight
    max_weight = 0 if len(weights) == 0 else max(weights.keys())
    return max_weight, weights


def insert_mnemonic(label: str, char: str) -> str:
    pos = label.lower().find(char)
    if pos >= 0:
        return label[:pos] + "&" + label[pos:]
    return label


def assign_mnemonics(menu: QMenu):
    # Collect actions
    actions = [a for a in menu.actions() if not a.isSeparator()]

    # Sequence map: mnemonic key -> QAction
    sequence_to_action: dict[str, QAction] = {}

    final_text: dict[QAction, str] = {}

    actions.reverse()

    while len(actions) > 0:
        action = actions.pop()
        label = action.text()
        _, weights = calculate_weights(label)

        chosen_char = None

        # Try candidates, starting from highest weight
        for weight in sorted(weights.keys(), reverse=True):
            c = weights[weight].lower()
            other = sequence_to_action.get(c)

            if other is None:
                chosen_char = c
                sequence_to_action[c] = action
                break
            else:
                # Compare weights with existing action
                other_max, _ = calculate_weights(remove_mnemonic_marker(other.text()))
                if weight > other_max:
                    # Take over from weaker action
                    actions.append(other)
                    sequence_to_action[c] = action
                    chosen_char = c

        # Apply mnemonic if found
        if chosen_char:
            plain = remove_mnemonic_marker(label)
            new_label = insert_mnemonic(plain, chosen_char)
            final_text[action] = new_label
        else:
            # No mnemonic assigned → clean text
            final_text[action] = remove_mnemonic_marker(label)

    for a, t in final_text.items():
        a.setText(t)
