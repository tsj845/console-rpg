import re

commentre = re.compile("~~.*~~\n?")
assignre = re.compile("[^\n]+ = [^\n]+\n?")
blockre = re.compile("\*\*[\w\s/]*\*\*\n?|\*&[\w\s]*\*\*\n?")

# lines
lines = []
with open("content.amly") as f:
    lines = f.read().split("```")

# final data list
datums = []

# parses a "document"
def parse (rawline : str):
    # checks that it's not empty
    if (rawline == ""):
        return
    # strips trailing newline
    rawline = rawline[:-1] if rawline[-1] == "\n" else rawline
    # removes comments
    matches = commentre.findall(rawline)
    for m in matches:
        rawline = rawline.replace(m, "", 1)
    # final data
    data = {}
    # block lines
    blocks = []
    # non-block lines
    nonblocks = []
    # nested block depth
    blockdepth = 0
    rawline = rawline.split("\n")
    for i in range(len(rawline)):
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
        # if (line[0] in ("startroom",)):
        #     specials.append(line)
        #     continue
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
    # splits by sep when outside of quotes
    def nqs (string : str, sep : str):
        f = string.split(sep)
        i = 0
        while i < len(f)-1:
            if (i >= len(f)):
                break
            if (f[i].count("\"") % 2 != 0):
                f[i] = f[i] + " " + f.pop(i+1)
            i += 1
        if (f[-1].count("\"") % 2 != 0):
            a = f.pop()
            f.append(f.pop() + " " + a)
        for i in range(len(f)):
            f[i] = f[i].replace("\"", "")
        return f
    # data structure parsing
    def datstruct (line : str):
        line = nqs(line[1:-1], " ")
        # print(line)
        struct = {"name":line.pop(0)}
        for x in line:
            x = x.split("=")
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
                    if (flatlist and blockdepth == 2):
                        cb.append({"list":[], "uid":blockname})
                        blockpath.append(len(cb)-1)
                        cb = cb[-1]
                    else:
                        cb[blockname] = {"list":[]}
                        cb = cb[blockname]
                        blockpath.append(blockname)
        # checks for assignment
        elif (assignre.match(line)):
            line = line.split(" = ")
            cb[line[0]] = line[1] if line[1][0] != "<" else datstruct(line[1])
        else:
            # print(cb)
            if (flatlist and blockdepth == 1):
                cb.append(datstruct(line))
            else:
                cb["list"].append(datstruct(line))
    # for i in range(len(specials)):
    #     line = specials[i]
    #     if (line[0] == "startroom"):
    #         data["startroom"] = _ret(data["rooms"], line[1])
    if (data["did"] == "2"):
        data["prog"] = 0
    # print("{")
    # for key in data.keys():
        # print(f"{key}: {data[key]}")
    # print("}")
    # print(data)
    # adds the data to the final list
    datums.append(data)

# removes empty lines
for i in range(lines.count("\n")):
    lines.pop(lines.index("\n"))

# parses data
for lineind in range(len(lines)):
    parse(lines[lineind])

print(datums[0])