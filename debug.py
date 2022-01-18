from helpers.encoder import encoder

def tse () -> None:
    try:
        with open("save.tssvf", "r") as f:
            data = f.read()
    except FileNotFoundError:
        return
    rer = ""
    if (data.startswith("{")):
        rer = encoder.encode(0xadfc, 1, data)
    else:
        rer = encoder.decode(data)
    with open("save.tssvf", "w") as f:
        f.write(rer)