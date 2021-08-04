#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# pylint: disable=C0103, W0703, R0201, R0902, R0912, R0914, R0915, R1702

"""
  pgjeeb.py
  MIT license (c) 2021 Asylum Computer Services LLC
  https://asylumcs.net
"""

import argparse
import os
import sys
import textwrap
import datetime
import regex as re

class Pgjeeb:
    """ UTF-8 Jeebies, new algorithm """

    def __init__(self, args):
        self.infile = args.infile
        self.outfile = args.outfile
        self.verbose = args.verbose
        self.hejee = []
        self.bejee = []
        self.hejeemap2 = dict()  # 2-word 'he' forms
        self.hejeemap3 = dict()  # 3-word 'he' forms
        self.bejeemap2 = dict()  # 2-word 'be' forms
        self.bejeemap3 = dict()  # 3-word 'be' forms
        self.wb = []  # working buffer
        self.encoding = ""  # UTF-8 or ISO-8859-1
        self.lastlookfor = ""
        self.runlog = []  # run reports to be sorted and sent to report[]
        self.report = []  # report that will be saved
        self.preok = []  # line number and 'do not check' 2-word forms
        self.sentences = []
        self.words = []
        self.words2 = []
        self.words3 = []
        self.wrapper = textwrap.TextWrapper()
        self.wrapper.break_long_words = False
        self.wrapper.break_on_hyphens = False
        self.root = os.path.dirname(os.path.realpath(__file__))

    def fatal(self, message):
        """ display fatal error and exit """
        sys.stderr.write("fatal: " + message + "\n")
        sys.exit(1)

    def load_file(self, fname):
        """loads a file from fname
        returns line buffer as UTF-8, no line terminators; returns self.encoding
        """
        try:
            t = open(fname, "r", encoding="utf-8").read()
            encoding = "UTF-8"
        except UnicodeDecodeError:
            t = open(fname, "r", encoding="latin-1").read()
            t = t.encode("utf-8").decode("latin-1")  # convert to UTF-8
            encoding = "ISO-8859-1"
        except Exception as e:
            self.fatal(
                "loadFile: cannot process source file {} {}".format(fname, str(e))
            )
        wb = t.split("\n")  # split into lines
        if encoding == "UTF-8":
            wb[0] = re.sub("\uFEFF", "", wb[0])  # remove BOM if present
        wb = [s.rstrip() for s in wb]
        while wb[-1] == "":  # no trailing blank lines
            wb.pop()
        for i, _ in enumerate(self.wb):
            self.wb[i] = re.sub(r"[’‘]", "'", self.wb[i])
            self.wb[i] = re.sub(r"[“”]", '"', self.wb[i])
        return (wb, encoding)

    def saveFile(self, b):
        """saves a buffer to self.outfile specified by user
        buffer is UTF-8, no BOM is added, uses CR/LF
        """
        with open(self.outfile, "w", encoding="UTF-8") as f:
            f.write("<pre>")
            f.write("pgjeeb run report\n")
            f.write(f"run started: {str(datetime.datetime.now())}\n");
            f.write("source file: {}\n".format(os.path.basename(self.infile)))
            f.write(f"<span style='background-color:#FFFFDD'>close this window to return to the UWB.</span>\n");
            f.write("\n")
            for s in b:
                f.write("{:s}\r\n".format(s))
            f.write("</pre>")

    def makemap_hejee(self):
        """
        a line in the he-utf8.jee file like this:
        |he|abruptly    125
        will generate an entry in the hejeemap2 dict like this:
        "|he|abruptly" -> 125
        three word forms into hejeemap3
        """
        for line in self.hejee:
            m = re.match(r"(\|he\|['\p{L}]+)\s+(\d+)", line)
            if m:
                self.hejeemap2[m.group(1)] = int(m.group(2))
            m = re.match(r"(\w+\|he\|\w+)\s+(\d+)", line)
            if m:
                self.hejeemap3[m.group(1)] = int(m.group(2))

    def makemap_bejee(self):
        """
        a line in the be-utf8.jee file like this:
        |be|accepted    32
        will generate an entry in the bejeemap2 dict like this:
        "|be|accepted" -> 32
        three word forms into bejeemap3
        "not|be|afraid" -> 1242
        """
        for line in self.bejee:
            m = re.match(r"(\|be\|['\p{L}]+)\s+(\d+)", line)
            if m:
                self.bejeemap2[m.group(1)] = int(m.group(2))
            m = re.match(r"(\w+\|be\|\w+)\s+(\d+)", line)
            if m:
                self.bejeemap3[m.group(1)] = int(m.group(2))

    def showcontext(self, s, lookfor, stats):
        """ highlighted single report """
        badness = f"{stats[0]} {stats[1]} {stats[2]} {stats[3]}"
        s2 = f"{s}"
        m = re.search(lookfor, s2, re.IGNORECASE)
        if m:
            if lookfor == self.lastlookfor:
                return
            if self.verbose:
                self.runlog.append(f"{lookfor} {badness}")
            else:
                self.runlog.append(f"{lookfor}")
            # print(m.group(0), m.span(), s2)
            s2 = re.sub(m.group(0), "☱" + m.group(0) + "☲", s2)
            t2 = self.wrapper.wrap(s2)
            for line in t2:
                self.runlog.append(f"    {line}")
            self.runlog.append("")
            self.lastlookfor = lookfor

    def myfindall(self, regex, searchstring):
        """ a findall that returns match objects, not strings """
        pos = 0
        while True:
            match = regex.search(searchstring, pos)
            if not match:
                return
            yield match
            pos = match.end()

    def buildReport(self):
        """ generates the HTML report, with highlighting """
        lastlinenum = ""
        lastlinelastword = ""
        # self.runlog.sort()
        for _,s in enumerate(self.runlog):
            s = s.replace(
                "☱",
                "<span style='border:1px solid silver; background-color:#FFFFAA'>",
            )
            s = s.replace("☲", "</span>")
            s = s.replace("☳", "be")
            s = s.replace("☶", "he")
            self.report.append(s)

    def split_into_sentences(self, text):
        """ regex approach """
        alphabets= "([A-Za-z])"
        digits = "([0-9])"
        prefixes = "(Mr|St|Mrs|Ms|Dr)[.]"
        suffixes = "(Inc|Ltd|Jr|Sr|Co)"
        starters = "(Mr|Mrs|Ms|Dr|He\s|She\s|It\s|They\s|Their\s|Our\s|We\s|But\s|However\s|That\s|This\s|Wherever)"
        acronyms = "([A-Z][.][A-Z][.](?:[A-Z][.])?)"
        websites = "[.](com|net|org|io|gov)"
        # begin split
        text = " " + text + "  "
        text = text.replace("\n"," ")
        text = re.sub(prefixes,"\\1<prd>",text)
        text = re.sub(websites,"<prd>\\1",text)
        if "Ph.D" in text: text = text.replace("Ph.D.","Ph<prd>D<prd>")
        text = re.sub("\s" + alphabets + "[.] "," \\1<prd> ",text)
        text = re.sub(acronyms+" "+starters,"\\1<stop> \\2",text)
        text = re.sub(digits + "[.]" + digits,"\\1<prd>\\2",text)
        text = text.replace("e.g.","e<prd>g<prd>")
        text = text.replace("...","<prd><prd><prd>")
        text = re.sub(alphabets + "[.]" + alphabets + "[.]" + alphabets + "[.]","\\1<prd>\\2<prd>\\3<prd>",text)
        text = re.sub(alphabets + "[.]" + alphabets + "[.]","\\1<prd>\\2<prd>",text)
        text = re.sub(" "+suffixes+"[.] "+starters," \\1<stop> \\2",text)
        text = re.sub(" "+suffixes+"[.]"," \\1<prd>",text)
        text = re.sub(" " + alphabets + "[.]"," \\1<prd>",text)
        if "”" in text: text = text.replace(".”","”.")
        if "\"" in text: text = text.replace(".\"","\".")
        if "!" in text: text = text.replace("!\"","\"!")
        if "?" in text: text = text.replace("?\"","\"?")
        text = text.replace(".",".<stop>")
        text = text.replace("?","?<stop>")
        text = text.replace("!","!<stop>")
        text = text.replace("<prd>",".")
        sentences = text.split("<stop>")
        sentences = sentences[:-1]
        sentences = [s.strip() for s in sentences]
        return sentences

    def parseBlob(self):
        """ text is loaded, maps are in place """
        s = ""
        for line in self.wb:
            s = s + " " + line
        s = s.strip()
        self.sentences = self.split_into_sentences(s)
        for _, sentence in enumerate(self.sentences):
            s2 = f"{sentence}"
            s3 = s2.replace("'", "☶")
            # find all two word forms for this sentence
            re2 = re.compile(r"\b(he|be)\s([\p{L}']+)")
            re3 = re.compile(r"([\p{L}']+)\s(he|be)\s([\p{L}']+)")
            s2 = s2.replace("’", "'")
            s2 = s2.lower()
            # parse 2-word forms
            s3 = s2
            t = []
            m = re.search(re2, s3)
            while m:
                # print(m.group(1), m.group(2))
                t.append(f"{m.group(1)} {m.group(2)}")
                cutpoint = m.span()[0] + len(m.group(1)) + 1  # for the space
                s3 = s3[cutpoint:]
                m = re.search(re2, s3)
            self.words2.append(t)
            # parse 3-word forms
            s3 = s2
            t = []
            m = re.search(re3, s3)
            while m:
                # print(m.group(1), m.group(2))
                t.append(f"{m.group(1)} {m.group(2)} {m.group(3)}")
                cutpoint = m.span()[0] + len(m.group(1)) + 1  # for the space
                s3 = s3[cutpoint:]
                m = re.search(re3, s3)
            self.words3.append(t)

    def look2words(self, thehe2look, thebe2look):
        """ look up occurrences of each form """

        # first check for exact match in 2-word maps
        if thehe2look in self.hejeemap2:
            he2count = self.hejeemap2[thehe2look]
        else:
            he2count = 0
        if thebe2look in self.bejeemap2:
            be2count = self.bejeemap2[thebe2look]
        else:
            be2count = 0

        # if not found in 2-word form, check 3-word substring
        # to|be|creeping 20
        # will|be|creeping 4
        # would|be|creeping 3
        #   therefore allow "be|creeping"
        if he2count == 0:
            for key in self.hejeemap3:
                if thehe2look in key:
                    he2count += self.hejeemap3[key]
        if be2count == 0:
            for key in self.bejeemap3:
                if thebe2look in key:
                    be2count += self.bejeemap3[key]

        return (he2count, be2count)

    def look3words(self, thehe3look, thebe3look):
        """ look up occurrences of each form """
        if thehe3look in self.hejeemap3:
            he3count = self.hejeemap3[thehe3look]
        else:
            he3count = 0
        if thebe3look in self.bejeemap3:
            be3count = self.bejeemap3[thebe3look]
        else:
            be3count = 0
        return (he3count, be3count)

    def abe2(self, s):
        """ analyze 2-word 'he' or 'be' form """
        # returns -1->NO, 0->NF, 1->OK
        t = s.split(" ")
        h2look = f"|he|{t[1]}"
        b2look = f"|be|{t[1]}"
        (he2count, be2count) = self.look2words(h2look, b2look)
        result = 3  # assume OK
        if he2count == 0 and be2count == 0:
            result = 2  # change to "not found"
        if s.startswith("be") and he2count > be2count:
            result = 1  # or "not ok"
        if s.startswith("he") and be2count > he2count:
            result = 1  # other form prevails
        return result, he2count, be2count

    def abe3(self, s):
        """ analyze 3-word 'he' or 'be' form """
        # returns -1->NO, 0->NF, 1->OK
        t = s.split(" ")
        h3look = f"{t[0]}|he|{t[2]}"
        b3look = f"{t[0]}|be|{t[2]}"
        (he3count, be3count) = self.look3words(h3look, b3look)
        result = 3  # assume OK
        if he3count == 0 and be3count == 0:
            result = 2  # change to "not found"
        if t[1] == "be" and he3count > be3count:
            result = 1  # or "not ok"
        if t[1] == "he" and be3count > he3count:
            result = 1  # other form prevails
        return result, he3count, be3count

    def scanBook(self):
        """ scan the book for reportable he/be suspects """
        for u, _ in enumerate(self.sentences):  # each sentence separately
            # print(f"{u:6} {self.sentences[u]}") ##
            i2 = 0  # index into 2-word forms
            i3 = 0  # index into 3-word forms

            # if the next 2-word form also ends the next 3-word form,
            # process them together, else do the 2-word by itself
            while i2 < len(self.words2[u]):
                if i3 < len(self.words3[u]) and self.words3[u][i3].endswith(
                    self.words2[u][i2]
                ):
                    # here we have a 2-word form ending a 3-word form
                    result = ""  # unknown for now
                    (a2, h2c, b2c) = self.abe2(
                        self.words2[u][i2]
                    )  # returns 0->NO, 1->NF, 2->OK
                    (a3, h3c, b3c) = self.abe3(self.words3[u][i3])
                    inx = a2 * 10 + a3
                    # print(inx)##
                    if result == "" and inx == 11:  # 2-word NO, 3-word NO -> NO
                        result = "NO"
                    if result == "" and inx == 12:  # 2-word NO, 3-word UK -> NO
                        result = "NO"
                    if result == "" and inx == 13:  # 2-word NO, 3-word OK -> OK
                        result = "OK"
                    if result == "" and inx == 21:  # 2-word UK, 3-word NO -> NO
                        result = "NO"
                    if result == "" and inx == 22:  # 2-word UK, 3-word UK -> NO
                        result = "NO"
                    if result == "" and inx == 23:  # 2-word UK, 3-word OK -> OK
                        result = "OK"
                    if result == "" and inx == 31:  # 2-word OK, 3-word NO -> NO
                        result = "NO"
                    if result == "" and inx == 32:  # 2-word OK, 3-word UK -> OK
                        result = "OK"
                    if result == "" and inx == 33:  # 2-word OK, 3-word OK -> OK
                        result = "OK"
                    if result == "NO":  # report suspect
                        ## print(f"{self.words3[u][i3]} (h2:{h2c} b2:{b2c} h3:{h3c} b3:{b3c})")
                        ## print(self.sentences[u])
                        ## print("-----------")
                        self.showcontext(
                            self.sentences[u], self.words3[u][i3], [h2c, b2c, h3c, b3c]
                        )
                    i3 += 1
                    i2 += 1
                else:
                    # process and advance 2-word form only
                    (a2, h2c, b2c) = self.abe2(
                        self.words2[u][i2]
                    )  # returns 1->NO, 2->NF, 3->OK
                    # print(f"{self.words2[u][i2]} he form: {h2c} be form: {b2c}")
                    if a2 < 3:
                        # report if NF or NO
                        ## print(f"{self.words2[u][i2]} (h2:{h2c} b2:{b2c})")
                        ## print(self.sentences[u])
                        ## print("-----------")
                        self.showcontext(
                            self.sentences[u], self.words2[u][i2], [h2c, b2c, 0, 0]
                        )
                    i2 += 1  # advance 2-word form only

    def run(self):
        """ runs the program """
        (self.wb, self.encoding) = self.load_file(self.infile)
        (self.hejee, _) = self.load_file(self.root+"/he-utf8.jee")
        (self.bejee, _) = self.load_file(self.root+"/be-utf8.jee")
        self.makemap_hejee()
        self.makemap_bejee()

        self.parseBlob()
        self.scanBook()
        # print(self.sentences[0]) ##
        # print(self.words2[0]) ##
        # print(self.words3[0]) ##
        self.buildReport()
        #for i,line in enumerate(self.report):
        #    print(i,line)
        self.saveFile(self.report)


# ===== main ==================================================================

PARSER = argparse.ArgumentParser(description="pgjeeb")
PARSER.add_argument("-i", "--infile", default="book.txt", help="input file")
PARSER.add_argument("-o", "--outfile", default="report.txt", help="output file")
PARSER.add_argument("-v", "--verbose", action="store_true", help="verbose statistics")
ARGS = PARSER.parse_args()
PGJEEB = Pgjeeb(ARGS)
PGJEEB.run()
