"""Jaro-Winkler string distance used by the brand value check."""

_PREFIX_LIMIT = 4
_PREFIX_SCALE = 0.1
_BOOST_THRESHOLD = 0.7


def jaro_winkler_distance(left: str, right: str) -> float:
    """Return Jaro-Winkler distance in the inclusive range from 0 to 1."""

    return 1.0 - _jaro_winkler_similarity(left, right)


def _jaro_winkler_similarity(left: str, right: str) -> float:
    if left == right:
        return 1.0
    if not left or not right:
        return 0.0

    left_length = len(left)
    right_length = len(right)
    match_distance = max(left_length, right_length) // 2 - 1
    match_distance = max(match_distance, 0)
    left_matches = [False] * left_length
    right_matches = [False] * right_length
    matches = 0

    for left_index, left_character in enumerate(left):
        start = max(0, left_index - match_distance)
        end = min(left_index + match_distance + 1, right_length)
        for right_index in range(start, end):
            if right_matches[right_index] or left_character != right[right_index]:
                continue
            left_matches[left_index] = True
            right_matches[right_index] = True
            matches += 1
            break

    if matches == 0:
        return 0.0

    right_index = 0
    transpositions = 0
    for left_index, is_match in enumerate(left_matches):
        if not is_match:
            continue
        while not right_matches[right_index]:
            right_index += 1
        if left[left_index] != right[right_index]:
            transpositions += 1
        right_index += 1

    jaro_similarity = (
        matches / left_length + matches / right_length + (matches - transpositions / 2.0) / matches
    ) / 3.0
    if jaro_similarity <= _BOOST_THRESHOLD:
        return jaro_similarity

    prefix_length = 0
    for left_character, right_character in zip(left[:_PREFIX_LIMIT], right[:_PREFIX_LIMIT], strict=False):
        if left_character != right_character:
            break
        prefix_length += 1
    return jaro_similarity + prefix_length * _PREFIX_SCALE * (1.0 - jaro_similarity)
