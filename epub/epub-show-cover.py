#!/usr/bin/env python3
# Author: Antonios Tsolis (Alamot)
import os
import sys
import zipfile
from lxml import etree
from PIL import Image


# Let's define the required XML namespaces
namespaces = {
   "calibre":"http://calibre.kovidgoyal.net/2009/metadata",
   "dc":"http://purl.org/dc/elements/1.1/",
   "dcterms":"http://purl.org/dc/terms/",
   "opf":"http://www.idpf.org/2007/opf",
   "u":"urn:oasis:names:tc:opendocument:xmlns:container",
   "xsi":"http://www.w3.org/2001/XMLSchema-instance",
   "xhtml":"http://www.w3.org/1999/xhtml"
}


def get_epub_cover(epub_path):
    ''' Return the cover image file from an epub archive. '''
    
    # We open the epub archive using zipfile.ZipFile():
    with zipfile.ZipFile(epub_path) as z:
    
        # We load "META-INF/container.xml" using lxml.etree.fromString():
        t = etree.fromstring(z.read("META-INF/container.xml"))
        # We use xpath() to find the attribute "full-path":
        '''
        <container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
          <rootfiles>
            <rootfile full-path="OEBPS/content.opf" ... />
          </rootfiles>
        </container>
        '''
        rootfile_path =  t.xpath("/u:container/u:rootfiles/u:rootfile",
                                             namespaces=namespaces)[0].get("full-path")
        print("Path of root file found: " + rootfile_path)
        
        # We load the "root" file, indicated by the "full_path" attribute of "META-INF/container.xml", using lxml.etree.fromString():
        t = etree.fromstring(z.read(rootfile_path))

        cover_href = None
        try:
            # For EPUB 2.0, we use xpath() to find a <meta> 
            # named "cover" and get the attribute "content":
            '''
            <metadata xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:opf="http://www.idpf.org/2007/opf">
              ...
              <meta content="my-cover-image" name="cover"/>
              ...
            </metadata>            '''

            cover_id = t.xpath("//opf:metadata/opf:meta[@name='cover']",
                                      namespaces=namespaces)[0].get("content")
            print("ID of cover image found: " + cover_id)
            # Next, we use xpath() to find the <item> (in <manifest>) with this id 
            # and get the attribute "href":
            '''
            <manifest>
                ...
                <item id="my-cover-image" href="images/978.jpg" ... />
                ... 
            </manifest>
            '''
            cover_href = t.xpath("//opf:manifest/opf:item[@id='" + cover_id + "']",
                                 namespaces=namespaces)[0].get("href")
        except IndexError:
            pass
        
        if not cover_href:
            # For EPUB 3.0, We use xpath to find the <item> (in <manifest>) that
            # has properties='cover-image' and get the attribute "href":
            '''
            <manifest>
              ...
              <item href="images/cover.png" id="cover-img" media-type="image/png" properties="cover-image"/>
              ...
            </manifest>
            '''
            try:
                cover_href = t.xpath("//opf:manifest/opf:item[@properties='cover-image']",
                                     namespaces=namespaces)[0].get("href")
            except IndexError:
                pass

        if not cover_href:
            # Some EPUB files do not declare explicitly a cover image.
            # Instead, they use an "<img src=''>" inside the first xhmtl file.
            try:
                # The <spine> is a list that defines the linear reading order
                # of the content documents of the book. The first item in the  
                # list is the first item in the book.  
                '''
                <spine toc="ncx">
                  <itemref idref="cover"/>
                  <itemref idref="nav"/>
                  <itemref idref="s04"/>
                </spine>
                '''
                cover_page_id = t.xpath("//opf:spine/opf:itemref",
                                        namespaces=namespaces)[0].get("idref")
                # Next, we use xpath() to find the item (in manifest) with this id 
                # and get the attribute "href":
                cover_page_href = t.xpath("//opf:manifest/opf:item[@id='" + cover_page_id + "']",
                                          namespaces=namespaces)[0].get("href")
                # In order to get the full path for the cover page,
                # we have to join rootfile_path and cover_page_href:
                cover_page_path = os.path.join(os.path.dirname(rootfile_path), cover_page_href)
                print("Path of cover page found: " + cover_page_path)     
                # We try to find the <img> and get the "src" attribute:
                t = etree.fromstring(z.read(cover_page_path))              
                cover_href = t.xpath("//xhtml:img", namespaces=namespaces)[0].get("src")
            except IndexError:
                pass

        if not cover_href:
            print("Cover image not found.")  
            return None

        # In order to get the full path for the cover image,
        # we have to join rootfile_path and cover_href:
        cover_path = os.path.join(os.path.dirname(rootfile_path), cover_href)
        print("Path of cover image found: " + cover_path)                
                
        # We return the image
        return z.open(cover_path)


if len(sys.argv) < 2:
    print("Usage: " + sys.argv[0] + " filename.epub")
    exit()

epubfile = sys.argv[1]
if not os.path.isfile(epubfile):
    print("File not found: " + epubfile)
    exit()

cover = get_epub_cover(epubfile)
if not cover:
    exit()
image = Image.open(cover)
image.show()


