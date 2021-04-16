#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Aug 16 10:25:52 2019

@author: robert
"""

import os
import numpy as np
from PIL import Image, ImageDraw

rot_angles = {90:Image.ROTATE_90,
              180:Image.ROTATE_180,
              270:Image.ROTATE_270}

flip_modes = {'hor':Image.FLIP_LEFT_RIGHT,
              'vert':Image.FLIP_TOP_BOTTOM}

class Tiling():
    '''
    Tool for slicing an image into square tiles of specified size. Requires PIL.
    
    Syntax:
        
        t = Tiling(size, stride)
        
    Parameterers:        
        
        size (int): tile width, equal to tile height.
        
        stride (int): tiling stride (by default stride = size).
        
    Methods:
        
        apply(source): applying the tiling to an image.
        
        get_tile_rects(): yields iterable of (left, top, right, bottom) tuples for every tile.

        get_tile_images(): yields iterable of tile images.
        
        write_tiles(target_dir): writes tiles as separate images into target_dir (by default "tiles" subfolder in source image folder).
        
    '''
    
    def __init__(self, size, stride=None):
        self.size = size
        if stride is None or stride < 1:
            self.stride = size
        else:
            self.stride = stride
        self.source = None
            
    def apply(self, source):
        '''
        Applying the tiling to an image.
        
        Syntax:
            
            t.apply(source)
            
        Parameter:
            
            source (str or PIL Image): image to tile. Can be filename or PIL image object.
        '''

        if type(source) is str:
            self.source = Image.open(source)
            self.source_name = os.path.split(source)[-1].split('.')[0]
        else:
            self.source = source
            self.source_name = ''
        (w, h) = self.source.size
        self.shape = ((h - self.size)//self.stride + 1,
                      (w - self.size)//self.stride + 1)
        self.n_tiles = self.shape[0]*self.shape[1]
            
    def get_tile_rects(self):
        '''
        Yielding iterable of (left, top, right, bottom) tuples for every tile.

        Syntax:
            
            rects = t.get_tile_rects()
            
        Yields:
            
            (left, top, right, bottom) tuples.
        
        '''
        if self.source is None:
            raise AttributeError('You should apply the tiling to an image before calling this method.')
        left, top = 0, 0
        while top < self.source.size[1]:
            while left < self.source.size[0]:
                yield (left, top, left+self.size, top+self.size)
                left += self.stride
            left = 0
            top += self.stride
            
    def get_tile_images(self):
        '''
        Yielding iterable of tile PIL images.

        Syntax:
            
            imgs = t.get_tile_images()
            
        Yields:
            
            PIL image objects.
        '''
        if self.source is None:
            raise AttributeError('You should apply the tiling to an image before calling this method.')
        left, top = 0, 0
        while top < self.source.size[1]:
            while left < self.source.size[0]:
                yield self.source.crop((left, top, 
                                       left+self.size, top+self.size))
                left += self.stride
            left = 0
            top += self.stride
            
    def write_tiles(self, target_dir='tiles', 
                    rotate=False,
                    flip=False,
                    filename_prefix = None):
        '''
        Writing tiles into separate .png files.
        
        Syntax:
            
            t.write_tiles(target_dir, rotate, flip, filename_prefix)
            
        Parameters:
            
            target_dir (str): directory to write tiles in (by default "./tiles")
            
            rotate (bool): in addition to original tile, write its copies rotated by 90, 180 and 270 degrees (by default False)
            
            flip (bool):  in addition to original tile, write its copies flipped horizontally and vertically (by default False)
            
            filename_prefix (str): the prefix part in a tile filename <PREFIX>_x_<LEFT>_y_<TOP>.png.
                                   If the source of tiling is a file, prefix is source file name by default.
                                   If the source of tiling is a PIL image, prefix is empty string by default.

        '''
        if filename_prefix is None:
            prefix = self.source_name
        else:
            prefix = filename_prefix
        tiles = self.get_tile_rects()
        if not os.path.exists(target_dir) or not os.path.isdir(target_dir):
            os.mkdir(target_dir)
        for tile in tiles:
            (left, top, right, bottom) = tile
            tilename = prefix+'_x_' +str(left).zfill(5)+'_y_'+str(top).zfill(5)
            crop = self.source.crop(tile)
            crop.save(os.path.join(target_dir, tilename+'.png'))
            if rotate:
                for angle in (90,180,270):
                    copyname = tilename+'_rot_'+str(angle)
                    copy = crop.transpose(rot_angles[angle])
                    copy.save(os.path.join(target_dir, copyname+'.png'))
            if flip:
                for flip_mode in ('vert', 'hor'):
                    copyname = tilename+'_flip_'+flip_mode
                    copy = crop.transpose(flip_modes[flip_mode])
                    copy.save(os.path.join(target_dir, copyname+'.png'))
                if rotate:
                    copy1 = copy.transpose(rot_angles[90])
                    copy1.save(os.path.join(target_dir, copyname+'_rot_90.png'))
                    copy1 = copy.transpose(rot_angles[270])
                    copy1.save(os.path.join(target_dir, copyname+'_rot_270.png'))
        tiles.close()
        
    def filter_tiles(self, 
                 lower_threshold = 0,
                 upper_threshold = 255
                 ):
        '''
        Filtering tiles with lower_threshold < mean pixel value < upper_threshold.
        
        Syntax:
            
            filtered = t.filter_tiles(lower_threshold, upper_threshold)
            
        Yields:
            
            (rect, PIL image) tuple
            
        '''
        rects = self.get_tile_rects()
        images = self.get_tile_images()
        for rect, image in zip(rects, images):
            mean_pix_val = np.asarray(image).mean()
            if mean_pix_val > lower_threshold and mean_pix_val < upper_threshold:
                yield rect,image
    
    def assemble(self, tiles, mode='RGB'):
        '''
        Assembling list (or other iterable) of tiles into the single image.

        Syntax:
            
            img = t.assemble(tiles, mode)
            
        Parameters:
            
            tiles (iterable): filenames or PIL Image objects or (rect,image) tuples. 
                              Image objects are expected to be non-flipped and non-rotated. 
                              If no rects given, images are expected to be pre-sorted in the assembling order:
                              from left to right, from top to bottom. 
                              If filenames given, they are expected to contain "x_<left>_y_<top>" 
                              substring. Filenames with "rot" or "flip" substrings
                              are ignored.
            
            mode (str): resulting image mode, "RGB" by default.
            
        Returns:
            
            PIL Image

        Examples:

            img = t.assemble( ['x_0_y_0.png', 'x_100_y_0.png'] )
            img = t.assemble( [left_top, right_top, left_bottom, right_bottom] ) # where left_top etc. are PIL images
            img = t.assemble( [(0,0,100,100), img1], [(100,0,200,100), img2] )   # where img1, img2 are PIL images
            
        '''
        rects = self.get_tile_rects()
        img = Image.new(mode, self.source.size)        
        for tile in tiles:
            if type(tile) is str:
                fname = os.path.split(tile)[-1]
                fname, ext = os.path.splitext(fname)
                fnamesplit = fname.split('_')
                if 'rot' in fnamesplit or 'flip' in fnamesplit:
                    continue
                try:
                    x_ind = fnamesplit.index('x')
                    y_ind = fnamesplit.index('y')
                    x = int(fnamesplit[x_ind+1])
                    y = int(fnamesplit[y_ind+1])
                except Exception:
                    raise ValueError('Filenames are expected to contain "x_<left>_y_<top>" substring.')
                tile_img = Image.open(tile, mode=mode)
                resp_rect = (x,y,x+self.size,y+self.size)
                img.paste(tile_img, resp_rect)
            elif type(tile) is tuple and len(tile) == 2:
                tile_img = tile[1]
                resp_rect = tile[0]
                img.paste(tile_img, resp_rect)
            else:
                tile_img = tile
                rect = next(rects)
                img.paste(tile_img, rect)
        return img
