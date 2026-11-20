# Bug: from_roman gets subtractive numerals wrong and accepts garbage

`from_roman("IX")` returns `11` (should be `9`) and `from_roman("MCMXCIV")` returns `2216` (should be `1994`).

It should also raise `ValueError` for anything that is not a valid canonical (uppercase, standard-form) Roman numeral between 1 and 3999, for example `"IIII"`, `"IC"`, `"VX"`, `"ABC"`, `"ix"` and `""`. Currently some of those return numbers.
