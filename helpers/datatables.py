n = None
# name sets for sets of items
itemnamesets = (
    # level 0 items
    (("homeless",0,n,"rag",n,n,"stick",n,n),("guy with a club",0,n,"rag","rag",n,n,"club",n,n)),
    # level 1 items
    (("unprepared",0,"hat","shirt","pants","socks","wooden sword",n,n),),
    (("grunt",0,"basic helm","basic plate","basic legs","basic boots","steel sword","steel shield",n)),
    (("dumb mage",1,"pointy hat","robes","pants","shoes","staff",n,"small mana bottle"))
)
# names for valid body slots
bodyslotnames = ("head","body","legs","boots","weapon","shield","charm")
# null stat dict
n = {"h":0,"d":0,"a":0,"s":0,"m":0}
# update
def u (base : dict, d : dict) -> dict:
    f = base.copy()
    for key in d.keys():
        f[key] = d[key]
    return f
# enemy stat minimums
enemymins = (
    (
        u(n,{"h":1,"a":1,"s":1}),
    ),
    (
        u(n,{"h":2,"a":1,"s":2}),
    ),
    (
        u(n,{"h":4,"a":2,"s":2}),
    ),
    (
        n,
        u(n,{"h":2,"a":0,"s":4,"m":2}),
    ),
)
# enemy stat maximums
enemymaxs = (
    (
        u(n,{"h":1,"a":1,"s":2}),
    ),
    (
        u(n,{"h":3,"a":2,"s":3}),
    ),
    (
        u(n,{"h":6,"a":4,"s":5}),
    ),
    (
        n,
        u(n,{"h":3,"a":1,"s":6,"m":6}),
    ),
)
# item stat minimums
itemmins = (
    (
        (
            (n,u(n,{"d":1}),n,n,u(n,{"a":1}),n,n),
            (n,u(n,{"d":1}),u(n,{"d":1}),n,n,u(n,{"a":1}),n,n),
        ),
    ),
    (
        (
            (*[u(n,{"d":1}) for i in range(4)],u(n,{"d":2}),n,n),
        ),
    ),
    (
        (
            (*[u(n,{"d":2}) for i in range(4)],u(n,{"a":2}),u(n,{"d":2}),n),
        ),
    ),
    (
        (),
        (
            (u(n,{"d":2}),*[u(n,{"d":1}) for i in range(3)],u(n,{"a":2}),n,u(n,{"m":2})),
        ),
    )
)
# item stat maximums
itemmaxs = (
    (
        (
            (n,u(n,{"d":1}),n,n,u(n,{"a":1}),n,n),
            (n,u(n,{"d":1}),u(n,{"d":1}),n,n,u(n,{"a":1}),n,n)
        ),
    ),
    (
        (
            (*[u(n,{"d":1}) for i in range(4)],u(n,{"d":2}),n,n),
        ),
    ),
    (
        (
            (*[u(n,{"d":2}) for i in range(4)],u(n,{"a":2}),u(n,{"d":2}),n),
        ),
    ),
    (
        (),
        (
            (u(n,{"d":2}),*[u(n,{"d":1}) for i in range(3)],u(n,{"a":2}),n,u(n,{"m":2})),
        ),
    )
)
# player item data
pitemmins = (
    (
        n,n,n,n,n,n,n
    ),
)
pitemmaxs = (
    (
        u(n,{"d":1,"h":1}),u(n,{"d":2,"h":1}),u(n,{"d":1,"s":1}),u(n,{"d":1,"s":1}),u(n,{"a":3,"s":2}),u(n,{"d":2}),u(n,{"m":1,"s":1,"h":1}),
    ),
)
pitemnames = (
    (
        ("iron helm", "basic helmet"),
        ("iron plating", "basic armor"),
        ("iron shinguards", "basic leg protectors"),
        ("iron boots", "basic footware"),
        ("steel sword", "blunt object"),
        ("wooden shield", "really bad damage blocker"),
        ("locket", "cursed item")
    ),
)