# Bug: median() is wrong for even-length lists

`median([1, 2, 3, 4])` returns `3`, but the median of an even-length list is the mean of the two middle values, `2.5`. Odd-length lists look fine.
