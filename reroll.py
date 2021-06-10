import requests
import numpy as np
from io import BytesIO
from PIL import Image, ImageEnhance

# API data keys we care about for images
keys = [
    'mini_base', 'pet', 'cloak', 'off_hand', 'body', 'hair', 'face', 'legs',
    'feet', 'chest', 'head', 'waist', 'hands', 'main_hand', 'horns', 'wings',
    'tattoo', 'ears', 'tail',
]

# Color Conversions
def rgb_to_hsv(rgb):
    # Translated from source of colorsys.rgb_to_hsv
    # r,g,b should be a numpy arrays with values between 0 and 255
    # rgb_to_hsv returns an array of floats between 0.0 and 1.0.
    rgb = rgb.astype('float')
    hsv = np.zeros_like(rgb)
    # in case an RGBA array was passed, just copy the A channel
    hsv[..., 3:] = rgb[..., 3:]
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    maxc = np.max(rgb[..., :3], axis=-1)
    minc = np.min(rgb[..., :3], axis=-1)
    hsv[..., 2] = maxc
    mask = maxc != minc
    hsv[mask, 1] = (maxc - minc)[mask] / maxc[mask]
    rc = np.zeros_like(r)
    gc = np.zeros_like(g)
    bc = np.zeros_like(b)
    rc[mask] = (maxc - r)[mask] / (maxc - minc)[mask]
    gc[mask] = (maxc - g)[mask] / (maxc - minc)[mask]
    bc[mask] = (maxc - b)[mask] / (maxc - minc)[mask]
    hsv[..., 0] = np.select(
        [r == maxc, g == maxc], [bc - gc, 2.0 + rc - bc], default=4.0 + gc - rc)
    hsv[..., 0] = (hsv[..., 0] / 6.0) % 1.0
    return hsv

def hsv_to_rgb(hsv):
    # Translated from source of colorsys.hsv_to_rgb
    # h,s should be a numpy arrays with values between 0.0 and 1.0
    # v should be a numpy array with values between 0.0 and 255.0
    # hsv_to_rgb returns an array of uints between 0 and 255.
    rgb = np.empty_like(hsv)
    rgb[..., 3:] = hsv[..., 3:]
    h, s, v = hsv[..., 0], hsv[..., 1], hsv[..., 2]
    i = (h * 6.0).astype('uint8')
    f = (h * 6.0) - i
    p = v * (1.0 - s)
    q = v * (1.0 - s * f)
    t = v * (1.0 - s * (1.0 - f))
    i = i % 6
    conditions = [s == 0.0, i == 1, i == 2, i == 3, i == 4, i == 5]
    rgb[..., 0] = np.select(conditions, [v, q, p, p, t, v], default=v)
    rgb[..., 1] = np.select(conditions, [v, v, v, q, p, p], default=t)
    rgb[..., 2] = np.select(conditions, [v, p, t, v, v, q], default=p)
    return rgb.astype('uint8')

def shift_hue(arr,hout):
    hsv=rgb_to_hsv(arr)
    hsv[...,0]=hout
    rgb=hsv_to_rgb(hsv)
    return rgb

# Use API to get character data
#url = 'https://api.reroll.co/api/characters/linkian209/29736'
url = 'https://api.reroll.co/api/characters/ghostoftherain/29948'
#url = 'https://api.reroll.co/api/characters/linkian209/32105'
response = requests.get(url)
if(response.status_code is 200):
    data = response.json()
    
    # Now loop through keys and compose the image
    img = None
    for key in keys:
        # Get content
        if(data[key] is not None):
            # Some keys have the image url in the asset item, if that exists, we will use that
            img_url = ''
            if('asset' in data[key]):
                img_url = data[key]['asset']['image_url']
            else:
                img_url = data[key]['image_url']
            
            # Get Image
            img_resp = requests.get(img_url)
            next_img = Image.open(BytesIO(img_resp.content)).convert("RGBA")
            x, y = next_img.size

            # Apply custom HSL
            hsl = {}
            if('hsl' in data[key]):
                hsl = data[key]['hsl']
            else:  
                hsl = data['{}_hsl'.format(key)]
            
            if(int(hsl['h']) != 360):
                next_img = Image.fromarray(shift_hue(np.array(next_img), hsl['h']), 'RGBA')

            if(hsl['s'] != 1):
                enhancer = ImageEnhance.Color(next_img)
                next_img = enhancer.enhance(hsl['s'])

            if(hsl['l'] != 1):
                enhancer = ImageEnhance.Brightness(next_img)
                next_img = enhancer.enhance(hsl['l'])

            # If the image does not exist, create it
            if img is None:
                img = Image.new("RGBA", (x, y), (255,255,255))
            
            img.paste(next_img, (0, 0, x, y), next_img)

    # Now show the image
    img.show()
