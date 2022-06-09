# -*- coding: utf-8 -*-
"""
Created on Wed Jun 27 20:58:35 2018

@author: andre
"""
#%%
from PIL import Image
import piexif
import piexif.helper
from PIL.ExifTags import TAGS

if __name__ == '__main__': 
    
    filename = 'fig2.jpg'
    new_file = 'fig2_new.jpg'
    im = Image.open(filename)
    exif_dict = piexif.load(im.info["exif"])
    # process im and exif_dict...
    #exif_dict["Exif"]["project"] = u"FDS"
    #exif_dict["Exif"]["branch"] = u"Data Collector Instance"
    #exif_dict["Exif"]["view"] = u"Overall flow of Data Collector Instance, Order Scheduler and Caster Scheduler."
    #exif_dict = piexif.load(filename)
    author = piexif.helper.UserComment.dump(u"dev")
    exif_dict["0th"][315] = "dev"  # Artist
    user_comment = piexif.helper.UserComment.dump(u"FDS|Data Collector Instance|id-275c3951-73ab-4bd4-b4f0-03db7bd568bb|1529938641083")
    exif_dict["Exif"][piexif.ExifIFD.UserComment] = user_comment
    exif_bytes = piexif.dump(exif_dict)
    #piexif.insert(exif_bytes, filename)
    
    im.save(new_file, "jpeg", exif=exif_bytes)
    
    #%%
    im = Image.open(new_file)
    exif_dict = piexif.load(im.info["exif"])
    
    #%%
    im = Image.open(new_file)    
    for (k,v) in im._getexif().items():
        print('%s = %s' % (TAGS.get(k), v))
    
    #%%
    with Image.open(new_file) as im:
        for segment, content in im.applist:
            marker, body = content.split(b"\x00", 1)
            #if segment == 'APP1' and marker == 'http://ns.adobe.com/xap/1.0/':
                # parse the XML string with any method you like
            print(body)
    #%%
    with open( filename, "rb") as fin:
        img = fin.read()
    imgAsString=str(img)
    xmp_start = imgAsString.find('<x:xmpmeta')
    xmp_end = imgAsString.find('</x:xmpmeta')
    if xmp_start != xmp_end:
        xmpString = imgAsString[xmp_start:xmp_end+12]
    
    #%%
    from pyavm import AVM
    from pyavm.extract import extract_xmp
    
    xmp = extract_xmp(filename, None)
    print(xmp)
    
    
    
    avm = AVM.from_image(filename)
    avm
    avm.embed(filename, new_file)
    avm = AVM.from_image(new_file)
    
    #%%
    from io import BytesIO
    from PIL import Image, TiffImagePlugin, TiffTags
    from PIL.ExifTags import TAGS
    from PIL.TiffImagePlugin import ImageFileDirectory_v2
    
    def get_exif(fn):
        ret = {}
        i = Image.open(fn)
        info = i._getexif()
        for tag, value in info.items():
            decoded = TAGS.get(tag, tag)
            ret[decoded] = value
        return ret
    
    print(get_exif(new_file))
    print_info(new_file)
    _TAGS_r = dict(((v, k) for k, v in TAGS.items()))
    
    #
    jpgimg1 = Image.open(filename)
    
    # Image File Directory
    ifd = ImageFileDirectory_v2()
    
    # TiffTags knows "Artist" (0x013b)
    TiffTags.lookup(_TAGS_r["Artist"])
    ifd[_TAGS_r["Artist"]] = u'somebody'
    ifd.tagtype[_TAGS_r['Artist']] = 2  # string, but you don't have to set explicitly.
    
    # TiffTags doesn't know "LightSource" (0x9208)
    TiffTags.lookup(_TAGS_r["LightSource"])
    ifd[_TAGS_r['LightSource']] = 1  # DayLight
    ifd.tagtype[_TAGS_r['LightSource']] = 3  # short, you must set.
    
    ##
    out = BytesIO()
    ifd.save(out)
    
    ## you must add magic number of exif structure
    exif = b"Exif\x00\x00" + out.getvalue()
    
    jpgimg1.save("out.jpg", exif=exif)