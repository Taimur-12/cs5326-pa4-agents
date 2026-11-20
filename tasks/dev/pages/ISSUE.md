# API pagination repeats and skips records

`paginate()` in `src/pages.py` serves our `/orders` API page by page, with the cursor helpers in `src/cursor.py`.
Client teams report:

- The last item of each page shows up again as the first item of the next page.
- After the final page they still get a `next_cursor`, and the page after that is empty.
- Results come back in insertion order, so pages shift when new orders arrive. They must be in key order.
- A tampered or truncated cursor crashes the server with a 500 (`binascii.Error`, `UnicodeDecodeError`, ...).
- `status` filtering makes pages come back short.

Contract:

- `paginate(items, page_size, cursor=None, key="id", status=None)` returns `{"items": [...], "next_cursor": ...}`.
- Items are dicts. They are ordered by `item[key]` ascending (keys are unique). If `status` is given, only items with
  `item["status"] == status` count: a page holds up to `page_size` **matching** items.
- `cursor` is `None` for the first page, otherwise a value returned as `next_cursor` by an earlier call; the page
  holds the items whose key is strictly greater than the key the cursor encodes.
- `next_cursor` is `None` when there are no further matching items, otherwise `encode_cursor(<key of the page's last
  item>)`.
- `page_size` must be an int from 1 to 100, else `ValueError`. Any cursor that `decode_cursor` cannot decode raises
  `ValueError`.
- Cursors are URL-safe base64 of JSON (`{"after": <key>}`); `decode_cursor(encode_cursor(k)) == k` for ints and
  strings.
