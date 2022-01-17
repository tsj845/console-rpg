from classes.ansi import ANSI
import re

class Exprs ():
    ## Exprs
    def base_strmod (*values):
        return re.compile(f"(?<!\\\\){'{'}({'|'.join(values)}){'}'}")
    red = base_strmod("red")
    orange = base_strmod("orange")
    yellow = base_strmod("yellow")
    green = base_strmod("green")
    lime = base_strmod("lime")
    blue = base_strmod("blue")
    sky = base_strmod("sky")
    violet = base_strmod("violet")
    stop = base_strmod("stop")
    __colors = [
        [(red, ANSI.red), (orange, ANSI.orange), (yellow, ANSI.yellow), (green, ANSI.dark_green), (lime, ANSI.light_green), (blue, ANSI.dark_blue), (sky, ANSI.light_blue), (violet, ANSI.violet), (stop, ANSI.default_text)],
        [(red, ANSI.help_red), (green, ANSI.help_green), (stop, ANSI.default_text)]
    ]
    def replace (string : str, *args):
        for arg in args:
            string = re.sub(arg[0], arg[1], string)
        return string
    def rep_colors (string : str, mapping : int = 0) -> str:
        return Exprs.replace(string, *Exprs.__colors[mapping])