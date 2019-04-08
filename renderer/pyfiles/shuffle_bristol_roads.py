import pickle, random as rd
road_nodes = "/map_data/road_points_bristol.pkl"
with open(road_nodes, 'rb') as f:
    locations = pickle.load(f)
print("{} Pointes were found".format(len(locations)))
rd.shuffle(locations)

road_nodes_shuffled = "/map_data/shuffled_road_points_bristol.pkl"
with open(road_nodes_shuffled, 'wb') as f:
    pickle.dump(locations, f)