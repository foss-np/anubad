#!/usr/bin/env python3

def edit(s1, s2):
    """
    >>> edit('this is a test', 'wokka wokka!!!')
    14
    """
    if len(s1) < len(s2): s1, s2 = s2, s1
    if len(s2) == 0: return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]


def hamming(s1, s2):
    """
    >>> hamming('this is a test', 'wokka wokka!!!')
    37
    """
    func = ord if type(s1) == str else lambda x: x
    s1 = ''.join([ "{0:08b}".format(func(c)) for c in s1 ])
    s2 = ''.join([ "{0:08b}".format(func(c)) for c in s2 ])
    return edit(s1, s2)


if __name__ == '__main__':
    import doctest
    doctest.testmod()
