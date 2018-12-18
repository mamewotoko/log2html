#! /usr/bin/env python
import glob
import os.path

RESULT_DIR='result'

with open('%s/index.html' % RESULT_DIR, 'w') as f:
    HEADER = """
<!DOCTYPE html>
<html lang="ja"><head>
   <meta charset="utf-8" />
   <meta name="Author" content="Takashi Masuyama" />
   <meta name="viewport" content="width=device-width" />
   <link rel="icon" href="ma.png" type="image/png" />
   <link rel="stylesheet" href="style.css" />
   <title>access log analysis result</title>
<body>
<h1>access log analysis result</h1>

<ol>
"""

    f.write(HEADER)
    for resultfile in glob.glob('%s/access*.html' % RESULT_DIR):
        basename = os.path.basename(resultfile)
        f.write("<li><a href=\"%s\">%s</a></li>" % (basename, basename))

    FOOTER = """
</ol>
</body>
</html>
"""
