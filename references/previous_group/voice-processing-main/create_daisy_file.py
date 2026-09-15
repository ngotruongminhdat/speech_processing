import os

opf_template = """<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE package
PUBLIC "+//ISBN 0-9673008-1-9//DTD OEB 1.2 Package//EN" "http://openebook.org/dtds/oeb-1.2/oebpkg12.dtd">
<package xmlns="http://openebook.org/namespaces/oeb-package/1.0/"
         unique-identifier="uid">
   <metadata>
      <dc-metadata>
         <dc:Format xmlns:dc="http://purl.org/dc/elements/1.1/">ANSI/NISO Z39.86-2005</dc:Format>
         <dc:Language xmlns:dc="http://purl.org/dc/elements/1.1/">vi-VN</dc:Language>
         <dc:Date xmlns:dc="http://purl.org/dc/elements/1.1/">2025-09-14</dc:Date>
         <dc:Publisher xmlns:dc="http://purl.org/dc/elements/1.1/">NXB Van Hoc</dc:Publisher>
         <dc:Title xmlns:dc="http://purl.org/dc/elements/1.1/">Hồi {num}</dc:Title>
         <dc:Identifier xmlns:dc="http://purl.org/dc/elements/1.1/" id="uid">9786043494594</dc:Identifier>
         <dc:Creator xmlns:dc="http://purl.org/dc/elements/1.1/">Thi Nai Am</dc:Creator>
      </dc-metadata>
      <x-metadata>
         <meta name="dtb:multimediaType" content="textNCX"/>
         <meta name="dtb:totalTime" content="0:00:00"/>
         <meta name="dtb:multimediaContent" content="text"/>
      </x-metadata>
   </metadata>
   <manifest>
      <item href="book.opf" id="opf" media-type="text/xml"/>
      <item href="dtbook.xml" id="opf-1" media-type="application/x-dtbook+xml"/>
      <item href="mo0.smil" id="mo0" media-type="application/smil"/>
      <item href="Hoi{num}.mp3" id="audio" media-type="audio/mpeg" />
      <item href="navigation.ncx"
            id="ncx"
            media-type="application/x-dtbncx+xml"/>
      <item href="resources.res"
            id="resource"
            media-type="application/x-dtbresource+xml"/>
   </manifest>
   <spine>
      <itemref idref="mo0"/>
   </spine>
</package>
"""

ncx_template = """<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE ncx
PUBLIC "-//NISO//DTD ncx 2005-1//EN" "http://www.daisy.org/z3986/2005/ncx-2005-1.dtd">
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">
   <head>
      <meta content="DAISY Pipeline 2" name="dtb:generator"/>
      <meta name="dtb:uid" content="9786043494594"/>
      <meta name="dtb:depth" content="01"/>
      <meta name="dtb:totalPageCount" content="0"/>
      <meta name="dtb:maxPageNumber" content="0"/>
      <smilCustomTest bookStruct="PAGE_NUMBER" defaultState="false" id="pagenum" override="visible"/>
      <smilCustomTest bookStruct="NOTE" defaultState="false" id="note" override="visible"/>
      <smilCustomTest bookStruct="NOTE_REFERENCE" defaultState="false" id="noteref" override="visible"/>
      <smilCustomTest bookStruct="ANNOTATION" defaultState="false" id="annotation" override="visible"/>
      <smilCustomTest bookStruct="LINE_NUMBER" defaultState="false" id="linenum" override="visible"/>
      <smilCustomTest bookStruct="OPTIONAL_SIDEBAR" defaultState="false" id="sidebar" override="visible"/>
      <smilCustomTest bookStruct="OPTIONAL_PRODUCER_NOTE" defaultState="false" id="prodnote" override="visible"/>
   </head>
   <docTitle>
      <text>Hồi {num}</text>
   </docTitle>
   <docAuthor>
      <text>Thi Nai Am</text>
   </docAuthor>
   <navMap>
      <navPoint playOrder="1" id="ncx-1">
         <navLabel>
            <text>Hồi {num}</text>
         </navLabel>
         <content src="mo0.smil#sid_4"/>
      </navPoint>
   </navMap>
</ncx>
"""

resources_template = """<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE resources
PUBLIC "-//NISO//DTD resource 2005-1//EN" "http://www.daisy.org/z3986/2005/resource-2005-1.dtd">
<resources xmlns="http://www.daisy.org/z3986/2005/resource/" version="2005-1">
   <scope nsuri="http://www.daisy.org/z3986/2005/ncx/">
      <nodeSet id="page-set" select="//smilCustomTest[@bookStruct='PAGE_NUMBER']">
         <resource xml:lang="en">
            <text>page</text>
         </resource>
      </nodeSet>
      <nodeSet id="note-set" select="//smilCustomTest[@bookStruct='NOTE']">
         <resource xml:lang="en">
            <text>note</text>
         </resource>
      </nodeSet>
      <nodeSet id="notref-set" select="//smilCustomTest[@bookStruct='NOTE_REFERENCE']">
         <resource xml:lang="en">
            <text>note</text>
         </resource>
      </nodeSet>
      <nodeSet id="annot-set" select="//smilCustomTest[@bookStruct='ANNOTATION']">
         <resource xml:lang="en">
            <text>annotation</text>
         </resource>
      </nodeSet>
      <nodeSet id="line-set" select="//smilCustomTest[@bookStruct='LINE_NUMBER']">
         <resource xml:lang="en">
            <text>line</text>
         </resource>
      </nodeSet>
      <nodeSet id="sidebar-set" select="//smilCustomTest[@bookStruct='OPTIONAL_SIDEBAR']">
         <resource xml:lang="en">
            <text>sidebar</text>
         </resource>
      </nodeSet>
      <nodeSet id="prodnote-set" select="//smilCustomTest[@bookStruct='OPTIONAL_PRODUCER_NOTE']">
         <resource xml:lang="en">
            <text>note</text>
         </resource>
      </nodeSet>
   </scope>
   <scope nsuri="http://www.w3.org/2001/SMIL20/">
      <nodeSet id="math-seq-set" select="//seq[@class='math']">
         <resource xml:lang="en">
            <text>mathematical formula</text>
         </resource>
      </nodeSet>
      <nodeSet id="math-par-set" select="//par[@class='math']">
         <resource xml:lang="en">
            <text>mathematical formula</text>
         </resource>
      </nodeSet>
   </scope>
</resources>
"""

def create_daisy_file(book_path, nav_path, res_path, i):
   # Tạo book.opf
   with open(book_path, "w", encoding="utf-8") as f:
      f.write(opf_template.format(num=i))

   # Tạo navigation.ncx
   with open(nav_path, "w", encoding="utf-8") as f:
      f.write(ncx_template.format(num=i))

   # Tạo resources.res (giữ nguyên)
   with open(res_path, "w", encoding="utf-8") as f:
      f.write(resources_template)

   print("✅ Đã tạo xong book.opf, navigation.ncx, resources.res")
