import pickle, random
from pynput import keyboard 
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import time, sys
from os import listdir

break_program = False

def on_press(Key):
    global break_program
    if Key == keyboard.Key.end:
        print('program aborted by user')
        break_program = True
        return False

def generate_triplet(tile_dir,locations):
    for location in locations:
        if break_program == True:
            plt.close()
            sys.exit()
        else:
            anchor = tile_dir + '/' + location + '_' + '0.png'
            positive = tile_dir + '/' + location + '_' + str(random.randint(1,20)) + '.png'        
            negative = tile_dir + '/' + random.choice(locations) + '_' + str(random.randint(1,20)) + '.png' 
            while location == negative:
                negative = tile_dir + '/' + random.choice(locations) + '_' + str(random.randint(1,20)) + '.png' 
            print("Anchor: " + anchor + "\n")
            print("Positive: " + positive + "\n")
            print("Negative: " + negative + "\n")         
            img_anchor = mpimg.imread(anchor)
            img_positive = mpimg.imread(positive)
            img_negative = mpimg.imread(negative)
            f, axarr = plt.subplots(1,3)
            axarr[0].imshow(img_anchor)
            axarr[1].imshow(img_positive)
            axarr[2].imshow(img_negative)
            plt.pause(2)                
            plt.close()
            
                
def extract_locations(tile_dir):
    files = []
    for name in listdir(tile_dir):
        nsplit = name.split('_')
        lat = nsplit[0]
        lon = nsplit[1]
        image_id = nsplit[2].split('.')[0]
        files.append(lat + '_' + lon )
    files = sorted(list(set(files)))
    return files

if __name__ == "__main__":		
    tile_dir = "/home/os17592/src/dkmkpy/renderer/images/roads"
    #tile_dir = "/images/ds0/"
    
    with keyboard.Listener(on_press=on_press) as listener:
        locations = extract_locations(tile_dir)
        generate_triplet(tile_dir,locations)
