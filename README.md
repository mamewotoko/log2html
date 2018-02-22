log2html
=========

Clustering log lines with difflib.SequenceMatcher as similarity measure,
display result as html table

Result 
------
![result image](img/log2html_demo.png)

Example1: clustering flake8 issues
----------------------------------

```
find . -name '*.py' | xargs flake8 | ./display_log.py -
```

Example2: clustering apache log
----------------------------------

```
./display_log.py /var/log/apache/error_log*
```

Example3: clustering adb log
-----------------------------
* TODO: write


Distributed analysis
----------------------
* dist_log.py

----
Takashi Masuyama < mamewotoko@gmail.com >  
http://mamewo.ddo.jp/

