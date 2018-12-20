
import re

if __name__ == '__main__':
    print("let's see")
    with open("/home/os17592/src/dkmkpy/renderer/map_data/mml/project.txt","r") as f:
        print("antes del for")
        for l in f:
            m = re.search(r'\"name\":\s\".*',l)
            if m:
                print(l)
                #print(m.group(0))
