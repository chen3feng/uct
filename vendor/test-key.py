import readchar


def print_key(key):
    for c in key:
        if c.isprintable():
            print(c, end='')
        else:
            print(fr'\x{ord(c):x}', end='')
    print()


def main():
    while True:
        key = readchar.readkey()
        print_key(key)
        if key == '\033':
            break


main()
