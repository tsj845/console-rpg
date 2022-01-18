import re
import sys
import os

_dev = False

if len(sys.argv) > 1 and sys.argv[1] == "-pt":
    _dev = True

assignre = re.compile("[^\n]+ = [^\n]+\n?")
blockre = re.compile("\*\*[\w\s/-]*\*\*\n?|\*&[\w\s-]*\*\*\n?")

# lines
lines = []
with open("content.amly" if not _dev else "pt.amly") as f:
    lines = f.read().split("```")

def _process_includes (lines : list) -> list:
    def getincludes (lin : str):
        lst = []
        with os.scandir(lin[:-1]) as dirs:
            for e in dirs:
                if (e.is_file()):
                    if (e.name.endswith(".amly")):
                        lst.append("$$include "+e.path)
                else:
                    lst.append("$$include "+e.path+"/")
        return lst
    def getinclude (lin : str) -> list:
        lst = []
        with open(lin, "r") as f:
            lst = f.read().split("```")
        _process_includes(lst)
        return lst
    l = lines.pop(0)
    lins = l.split("\n")
    i = 0
    while i < len(lins):
        lin = lins[i]
        if (lin.startswith("$$include")):
            lin : str = lin.split(" ", 1)[1]
            if (lin.endswith("/")):
                lins.extend(getincludes(lin))
            else:
                lines.extend(getinclude(lin))
        i += 1

if ("$$include" in lines[0]):
    _process_includes(lines)

# final data list
datums = []

# splits by sep when outside of quotes
def nqs (string : str, sep : str):
    string = string.split("\"")
    for i in range(0, len(string), 2):
        string[i] = string[i].replace(sep, "\x1c")
    for i in range(1, len(string), 2):
        string[i] = "\"" + string[i] + "\""
    string = "".join(string)
    ol = len(string)
    for i in range(ol):
        i = ol - i - 1
        if (string[i] == ""):
            string.pop(i)
    return string.split("\x1c")

# print(nqs('x="y z 1" n', " "))

# parses a "document"
def parse (rawline : str):
    # checks that it's not empty
    if (rawline == ""):
        return
    # strips trailing newline
    rawline = rawline[:-1] if rawline[-1] == "\n" else rawline
    # final data
    data = {}
    # block lines
    blocks = []
    # non-block lines
    nonblocks = []
    # nested block depth
    blockdepth = 0
    rawline = rawline.split("\n")
    ol = len(rawline)
    # removes whitespace and comments
    for i in range(ol):
        i = ol - i - 1
        rawline[i] = rawline[i].strip()
        l = rawline[i]
        if (l.startswith("~~")):
            rawline.pop(i)
        else:
            rawline[i] = l.replace("\\n", "\n")
    for i in range(len(rawline)):
        rawline[i] = rawline[i].lstrip()
        # checks if line has block syntax
        if (blockre.match(rawline[i])):
            # alias
            s = rawline[i]
            # gets block syntax instances
            found = blockre.findall(s)
            for j in range(len(found)-1):
                f = found[j]
                # stuff before block
                p1 = s[:s.index(f)]
                # checks non-zero length and adds
                if (len(p1)):
                    nonblocks.append(p1)
                # stuff until next instance of block syntax
                p2 = s[s.index(f):s.index(found[j+1])+(len(found[j+1]) if j == len(found)-2 else 0)]
                # moves to next instance of block syntax
                s = s[s.index(found[j+1]):]
                blocks.append(p2)
                # handles depth changes
                if ("/" in f):
                    blockdepth -= 1
                else:
                    blockdepth += 1
            # if there was only one instance do same things but to end of line instead of to next instance
            if (len(found) == 1):
                f = found[0]
                p1 = s[:s.index(f)]
                if (len(p1)):
                    nonblocks.append(p1)
                blocks.append(s[s.index(f):])
            # handle depth changes for last instance
            if ("/" in found[-1]):
                blockdepth -= 1
            else:
                blockdepth += 1
        # checks if currently in a block
        elif (blockdepth > 0):
            blocks.append(rawline[i])
        else:
            nonblocks.append(rawline[i])
    specials = []
    # handles simple lines
    for line in nonblocks:
        if (not len(line)):
            continue
        line = line.split(" = ")
        data[line[0]] = line[1]
    blockdepth = 0
    # path to current block
    blockpath = []
    # current block
    cb = data
    # gets current block using blockpath
    def getcb ():
        tmp = data
        for step in blockpath:
            tmp = tmp[step]
        return tmp
    # data structure parsing
    def datstruct (line : str):
        line = nqs(line[1:-1], " ")
        # print(line)
        struct = {"type":line.pop(0)}
        for x in line:
            x = x.split("=")
            # print(x)
            if (x[1][0] == "\""):
                x[1] = x[1][1:-1]
            struct[x[0]] = x[1]
        return struct
    flatlist = False
    # parses blocks
    for line in blocks:
        # checks non-zero length
        if (not len(line)):
            continue
        # checks if it's block syntax
        if (blockre.match(line)):
            # checks if closing block
            if ("/" in line):
                blockdepth -= 1
                blockpath.pop()
                cb = getcb()
                if (blockdepth == 0):
                    flatlist = False
                elif (type(cb) == list):
                    flatlist = True
                else:
                    flatlist = False
            else:
                # creates new block
                blockdepth += 1
                blockname = line[2:-2]
                if (line[1] == "&"):
                    cb[blockname] = []
                    flatlist = True
                    cb = cb[blockname]
                    blockpath.append(blockname)
                else:
                    if (flatlist):
                        cb.append({"list":[], "uid":blockname})
                        blockpath.append(len(cb)-1)
                        cb = cb[-1]
                    else:
                        # print(cb, blockpath)
                        cb[blockname] = {"list":[]}
                        cb = cb[blockname]
                        blockpath.append(blockname)
                    flatlist = False
        # checks for assignment
        elif (assignre.match(line)):
            line = line.split(" = ")
            cb[line[0]] = line[1] if line[1][0] != "<" else datstruct(line[1])
        else:
            # print(cb)
            if (flatlist):
                cb.append(datstruct(line))
            else:
                cb["list"].append(datstruct(line))
    if (data["did"] == "2"):
        data["prog"] = 0
    # adds the data to the final list
    datums.append(data)

# removes empty lines
for i in range(lines.count("\n")):
    lines.pop(lines.index("\n"))

# parses data
for lineind in range(len(lines)):
    parse(lines[lineind])

if (_dev):
    print(*datums, sep="\n\n")