import logging
logger = logging.getLogger()

import json, os, random, math
import pickle 

from my_utils import MyTimer, MyStruct

class Map:
  def __init__(self, path):
    self.path = path

    grid_cache_path = os.path.join(path, "cache_backend_grid.pickle")

    if os.path.isfile(grid_cache_path):
      logger.info("loading cached self.grid from %s", grid_cache_path)
      with open(grid_cache_path, 'rb') as f:
        self.grid = pickle.load(f)
    else:
      grid_path = os.path.join(path, "grid_save.json")
      self.loadGrid(grid_path)
      self.gridBFSAllPath()
      logger.info("caching self.grid to %s", grid_cache_path)
      with open(grid_cache_path, 'wb') as f:
        pickle.dump(self.grid, f)

    map_path = os.path.join(path, "map_save.json")
    self.loadMap(map_path)

  def getPath(self, cxy_s, cxy_t, add_random = False):
    path = [cxy_t]; g = self.grid;
    xy_now = self.getTile(cxy_t).xy
    xy_s = self.getTile(cxy_s).xy
    while (xy_now != xy_s):
      xy_now = g[xy_s].path[xy_now]
      if (xy_now != xy_s):
        path = [g[xy_now].cxy] + path
        if add_random and random.random() < 0.1:
          xy_mov = random.choice([(-1,0), (1,0), (0,1), (0,-1)])
          xy_new = (xy_now[0] + xy_mov[0], xy_now[1] + xy_mov[1])
          if xy_new != xy_s and g[xy_new].can_walk:
            path = [g[xy_new].cxy] + path
            #print('random', xy_now, xy_new)
            xy_now = xy_new
    path = [cxy_s] + path
    return path
  
  def getTile(self, c):
    return self.grid[math.floor(c[0]), math.floor(c[1])]
  
  def getCloseTile(self, c, add_random = False, condition = "can_walk"):
    assert(condition == "can_walk")
    rand_thres = 0.5 if add_random else 1.0;
    dis_min = 100000; tile_min = None;
    g = self.grid;
    for x, y in g:
      if (g[x,y].can_walk and math.dist(g[x,y].cxy, c) < dis_min):
        if ((not add_random) or (tile_min is None) or (random.random() < rand_thres)):
          dis_min = math.dist(g[x,y].cxy, c); tile_min = g[x,y];
    return tile_min;
  
  def getRandItem(self, closeto_c = None, closeto_dis = 20.0):
    try_co = 0;
    while (try_co < 20):
      item = random.choice(self.item_l); try_co += 1;
      if (not closeto_c is None):
        if (math.dist(closeto_c, (item.cx, item.cy)) <= closeto_dis):
          return item
      else:
        return item;
    return item
  
  def gridBFSAllPath(self):
    g = self.grid
    logger.info("building path for all tile pairs")
    for x, y in g:
      if (x % 20 == 0 and y % 40 == 0):
        print('x y:', x, y);
      if g[x,y].can_walk:
        p = g[x,y].path
        p[x,y] = [(x,y)]
        stack = [(x, y)]; cur_i = 0;
        while (cur_i < len(stack)):
          cur_x, cur_y = stack[cur_i]; cur_i += 1;
          for mx, my in [(1,0), (-1, 0), (0, 1), (0, -1)]:
            new_x, new_y = cur_x + mx, cur_y + my;
            if (g[new_x, new_y].can_walk) and (not (new_x, new_y) in p):
              p[new_x, new_y] = (cur_x, cur_y) #only saves the parent
              stack.append((new_x, new_y))
        assert(len(stack) == self.tile_can_walk_co)
              

  def loadGrid(self, grid_path):
    logger.info("Loading grid from %s", grid_path)
    with open(grid_path) as f:
      d = json.load(f)

    g = {}; can_walk_co = 0; minx, maxx, miny, maxy = 10000, -10000, 10000, -10000;
    self.grid = g
    for ps in d:
      x = int(ps.split('_')[0]); y = int(ps.split('_')[1]);
      minx = min(minx, x); maxx = max(maxx, x); miny = min(miny, y); maxy = max(maxy, y);
      assert(not (x,y) in g)
      tile = MyStruct(cx = x + 0.5, cy = y + 0.5, cxy = (x + 0.5, y + 0.5), x = x, y = y, xy = (x, y), can_walk = False, path = {})
      if "GridCanWalk," in d[ps]:
        tile.can_walk = True;
        can_walk_co += 1
      g[x,y] = tile

    logger.info("expanding the grid by 5 tiles for easier bfs")
    for x in range(minx - 5, maxx + 6):
      for y in range(miny - 5, maxy + 6):
        if not (x,y) in g:
          tile = MyStruct(cx = x + 0.5, cy = y + 0.5, cxy = (x + 0.5, y + 0.5), x = x, y = y, xy = (x, y), can_walk = False, path = {})
          g[x,y] = tile

    logger.info("can_walk_count: %d", can_walk_co); self.tile_can_walk_co = can_walk_co;
    #print(self.grid[7][76].can_walk)

  
  def loadMap(self, path):
    logger.info("Loading map from %s", path)
    with open(path) as f:
      d = json.load(f)

    sd = {}; self.sector_d = sd;
    self.sector_l = []
    # first, scan for first-level sector
    for k in d:
      if ("UI_Sector" in k and (":Name" in k) and (not "_" in d[k])):
        sec_name = d[k].replace('\n','')
        u_name = k.split(":")[0]
        assert(not sec_name in sd)
        pp = [float (x) for x in d[u_name + ":Draw"].split("_")]
        c_lowerleft = MyStruct(cx = min(pp[0], pp[2]), cy = min(pp[1], pp[3]))
        c_upperright = MyStruct(cx = max(pp[0], pp[2]), cy = max(pp[1], pp[3]))
        ss = MyStruct(name = sec_name, u_name = u_name, area_d = {}, c_ll = c_lowerleft, c_ur = c_upperright)
        sd[sec_name] = ss; self.sector_l.append(ss);
    logger.info('first-level sectors: %s', str(sd.keys()))

    self.area_l = []
    # second, scan for second-level area, each area should belong to one sector
    for k in d:
      if ("UI_Sector" in k and (":Name" in k) and ("_" in d[k])):
        assert(len(d[k].split("_")) == 2)
        sec_name = d[k].split("_")[0].replace('\n','')
        area_name = d[k].split("_")[1].replace('\n','')
        assert(sec_name in sd)
        u_name = k.split(":")[0]
        assert(not area_name in sd[sec_name].area_d)
        pp = [float (x) for x in d[u_name + ":Draw"].split("_")]
        c_lowerleft = MyStruct(cx = min(pp[0], pp[2]), cy = min(pp[1], pp[3]))
        c_upperright = MyStruct(cx = max(pp[0], pp[2]), cy = max(pp[1], pp[3]))
        #logger.info("area %s belongs to sector %s", area_name, sec_name)
        aa = MyStruct(name = area_name, sec_name = sec_name, u_name = u_name, item_l = [], c_ll = c_lowerleft, c_ur = c_upperright)
        sd[sec_name].area_d[area_name] = aa; self.area_l.append(aa);

    for sec_name in self.sector_d:
      if (len(sd[sec_name].area_d) == 0): #for any sector without any area, we will directly use it self as the area
        aa = MyStruct(name = sec_name, sec_name = sec_name, u_name = sd[sec_name].u_name, item_l = [], c_ll = sd[sec_name].c_ll, c_ur = sd[sec_name].c_ur)
        sd[sec_name].area_d[sec_name] = aa; self.area_l.append(aa);
        logger.info("sector %s has no area, using itself as the area name...", sec_name)

    self.item_l = []
    # third, scan for items, each item should belong to one area
    for k in d:
      if ("UI_Item" in k and (":Name" in k)):
        item_name = d[k].replace('\n','')
        u_name = k.split(":")[0]
        posl = d[u_name + ":Position"].split("_")
        cx, cy = float(posl[0]), float(posl[1])
        area_found = False
        for area in self.area_l:
          if (cx >= area.c_ll.cx and cy >= area.c_ll.cy and cx <= area.c_ur.cx and cy <= area.c_ur.cy):
            item = MyStruct(name = item_name, area_name = area.name, sec_name = area.sec_name, u_name = u_name, cx = cx, cy = cy, cxy = (cx, cy))
            # items could have the same name, so, i use list here
            area.item_l.append(item); self.item_l.append(item);
            area_found = True
            logger.info("item %s belongs to area %s, sector %s", item_name, area.name, area.sec_name)
        #print(item_name, posl)
        assert(area_found)

    logger.info("loaded %d sectors, %d areas, %d items", len(self.sector_l), len(self.area_l), len(self.item_l))
