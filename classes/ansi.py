class ANSI ():
    # ANSI COLORS
    help_green = "\x1b[38;2;18;188;121m"
    help_red = "\x1b[205;49;49m"
    health_high = "\x1b[38;2;0;200;0m"
    health_medium = "\x1b[38;2;245;245;0m"
    health_low = "\x1b[38;2;245;0;0m"
    red = "\x1b[38;2;175;0;0m"
    orange = "\x1b[38;2;240;150;0m"
    yellow = "\x1b[38;2;245;245;0m"
    light_green = "\x1b[38;2;0;200;0m"
    dark_green = "\x1b[38;2;0;175;0m"
    light_blue = "\x1b[38;2;0;175;255;0m"
    dark_blue = "\x1b[38;2;50;255;0m"
    violet = "\x1b[38;2;200;100;200m"
    fow_color = "\x1b[38;2;125;125;125m"
    default_text = "\x1b[39m"
    default_background = "\x1b[49m"
    # ANSI effects
    italic = "\x1b[3m"
    unitalic = "\x1b[23m"
    bold = "\x1b[1m"
    faint = "\x1b[2m"
    normal_intensity = "\x1b[22m"
    underline = "\x1b[4m"
    nounderline = "\x1b[24m"
    strike = "\x1b[9m"
    unstrike = "\x1b[29m"
    reset = "\x1b[0m"
    # characters
    empty_heart = "\u2661"
    heart = "\u2665"
    horizontal_light = "\x1b[1m\u2500\x1b[22m"
    vertical_light = "\x1b[1m\u2502\x1b[22m"
    corner_rd_light = "\x1b[1m\u250c\x1b[22m"
    corner_tr_light = "\x1b[1m\u2514\x1b[22m"
    corner_dl_light = "\x1b[1m\u2510\x1b[22m"
    corner_lt_light = "\x1b[1m\u2518\x1b[22m"
    joint_lur_light = "\x1b[1m\u2534\x1b[22m"
    joint_urd_light = "\x1b[1m\u251c\x1b[22m"
    joint_rdl_light = "\x1b[1m\u252c\x1b[22m"
    joint_dlt_light = "\x1b[1m\u2524\x1b[22m"
    cross_light = "\x1b[1m\u253c\x1b[22m"
    # movement
    mv_up = "\x1b[1A"
    mv_dn = "\x1b[1B"
    mv_rt = "\x1b[1C"
    mv_lf = "\x1b[1D"
    # functions
    def foreground (r : int, g : int, b : int) -> str:
        return f"\x1b[38;2;{r};{g};{b}m"
    def background (r : int, g : int, b : int) -> str:
        return f"\x1b[48;2;{r};{g};{b}m"
    def __getitem__ (self, key : str) -> str:
        _dct = {"c-tr":ANSI.corner_tr_light,"c-rd":ANSI.corner_rd_light,"c-dl":ANSI.corner_dl_light,"c-lt":ANSI.corner_lt_light,"l-hl":ANSI.horizontal_light,"l-vl":ANSI.vertical_light,"t-lur":ANSI.joint_lur_light,"t-urd":ANSI.joint_urd_light,"t-rdl":ANSI.joint_rdl_light,"t-dlu":ANSI.joint_dlt_light,"cross-l":ANSI.cross_light}
        out = ""
        for piece in key.split(","):
            out += _dct[piece]
        return out

Ansi = ANSI()