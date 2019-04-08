#Python 3
#import urllib.request, os
#Python2
from urllib2 import urlopen
import pickle, re, cv2, random as rd, numpy as np
import xml.etree.ElementTree as ET

class GSV:
    def __init__(self, lat, lon, zoom):      
        def get_pano_list(xml_url):
            pano_id_list = []
            response = urlopen(xml_url)
            tree = ET.parse(response)  
            root =tree.getroot()
            data_properties = root.find('data_properties')
            if data_properties == None:
                pano_id_list.append(None)
            else:
                pano_id = data_properties.get('pano_id')
                pano_id_list.append(pano_id)
                for prop in root.findall('annotation_properties'):
                    if prop != []:
                        for link in prop.findall('link'):
                            pano_id = link.get('pano_id')
                            pano_id_list.append(pano_id)
            return pano_id_list

        self.dir = 'gsv/'
        self.lat = lat
        self.lon = lon
        self.zoom = zoom
        self.xml_url = 'http://maps.google.com/cbk?output=xml&ll=' + str(lat) + ',' + str(lon)
        self.pano_list = get_pano_list(self.xml_url)
    
    def pano_list_as_bytes(self):
        if self.pano_list != [None]:
            id_list = []
            for pano_id in self.pano_list:
                id_list.append(pano_id.encode('utf-8'))
        else:
            id_list = [None]
        return id_list
    
    def url_to_image(self, url):
        resp = urlopen(url)
        image = np.asarray(bytearray(resp.read()), dtype="uint8")
        image = cv2.imdecode(image, cv2.IMREAD_COLOR)
        return image

    def concatenate_tiles(self, pano_id):
        x_range = [0,1]
        y_range = [0]
        pano = np.zeros((512*len(y_range), 512*len(x_range), 3), dtype= 'uint8')
        for x in x_range:
            for y in y_range:
                tile_url = 'http://maps.google.com/cbk?output=tile&zoom=' + str(self.zoom) + '&x=' +str(x)+ '&y=' + str(y) +'&cb_client=maps_sv&fover=2&onerr=3&renderer=spherical&v=4&panoid=' + pano_id
                img = GSV.url_to_image(self, tile_url)
                pano[512*y:512*(y+1), 512*x:512*(x+1),...] = img
        return pano

    def show_images(self, one_or_all):
        if self.pano_list != [None]:
            if one_or_all == "all":
                for pano_id in self.pano_list:
                    image = GSV.concatenate_tiles(self, pano_id)
                    cv2.imshow("Image_window",image)
                    cv2.waitKey(0)
            else:
                pano_id = self.pano_list[0]
                image = GSV.concatenate_tiles(self, pano_id)
                cv2.imshow("Image_window",image)
                cv2.waitKey(0)
                    
        else:
            print("Empty pano_id list")
    
    def download(self, option):
        images = []
        for pano_id in self.pano_list:
            image = GSV.concatenate_tiles(self, pano_id)
            image = cv2.resize(image, (224, 224))
            images.append(image)
        if option == "decoded_list":
            return images
        elif option == "tensor":
            tensor = np.stack(images)
            return tensor
        elif option == "list":
            images_list = []
            for image in images:
                image_string = cv2.imencode('.jpg', image)[1].tostring()
                images_list.append(image_string)
            return images_list
    
    def show_info(self):
        print("Pano_id list: ", self.pano_list)
        print("location: lat: {}, lon: {}".format(self.lat, self.lon))
        

#gsv1 = GSV(51.45532,-2.6017908, 1)
#gsv1.show_images(51.45532,-2.6017908, 1)
#gsv1.show_info()
#data = gsv1.download("tensor")
#print(np.shape(data))
#GSV.print_info(gsv1)
