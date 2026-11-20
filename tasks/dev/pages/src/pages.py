"""Cursor pagination over a list of records. See ISSUE.md."""
from .cursor import decode_cursor, encode_cursor


def paginate(items, page_size, cursor=None, key="id", status=None):
    start = 0
    if cursor is not None:
        after = decode_cursor(cursor)
        for i, item in enumerate(items):
            if item[key] == after:
                start = i
                break
    page = items[start:start + page_size]
    if status is not None:
        page = [it for it in page if it["status"] == status]
    next_cursor = encode_cursor(page[-1][key]) if page else None
    return {"items": page, "next_cursor": next_cursor}
