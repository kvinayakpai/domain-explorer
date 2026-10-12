"""Inline the dataset into the viewer template and write one self-contained index.html.

Usage: python viewer/assemble.py <dataset.json> <output index.html>
"""
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).parent
head = (HERE / "src/head.html").read_text(encoding="utf-8")
body = (HERE / "src/body.html").read_text(encoding="utf-8")
data = (
    pathlib.Path(sys.argv[1]).read_text(encoding="utf-8")
    .replace("</", "<\\/").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")
)
assert body.count("/*__DATA__*/") == 1, "data placeholder missing"
body = body.replace("/*__DATA__*/", data)
title = re.search(r"<title>.*?</title>", head, re.S).group(0)
rest = head.replace(title, "", 1)
page = (
    '<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
    '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">\n'
    + title + "\n" + rest + "\n</head>\n<body>\n" + body + "\n</body>\n</html>\n"
)
pathlib.Path(sys.argv[2]).write_text(page, encoding="utf-8")
print("wrote", sys.argv[2], len(page) // 1024, "KB")
