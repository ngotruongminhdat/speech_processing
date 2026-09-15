import xml.etree.ElementTree as ET
import re

def export_navmap(dtbook_file, output_nav="toc.ncx"):
    ns = {'dtb': 'http://www.daisy.org/z3986/2005/dtbook/'}
    tree = ET.parse(dtbook_file)
    root = tree.getroot()

    lessons = []
    for sent in root.findall(".//dtb:sent", ns):
        text = (sent.text or "").strip()
        if re.search(r"\bBài\s+\d+\b", text):
            lessons.append({
                "id": sent.attrib.get("id"),  # ví dụ: id_55
                "text": text
            })

    # Tạo cây XML cho navMap
    navMap = ET.Element("navMap")
    play_order = 1

    for lesson in lessons:
        navPoint = ET.SubElement(navMap, "navPoint", {
            "playOrder": str(play_order),
            "id": f"ncx-{play_order}"
        })

        navLabel = ET.SubElement(navPoint, "navLabel")
        text_el = ET.SubElement(navLabel, "text")
        text_el.text = lesson["text"]

        sid = lesson["id"].replace("id_", "sid_")
        content = ET.SubElement(navPoint, "content", {
            "src": f"mo0.smil#{sid}"
        })

        play_order += 1

    # Ghi ra file
    tree_out = ET.ElementTree(navMap)
    ET.indent(tree_out, space="   ", level=0)  # Python 3.9+ hỗ trợ indent
    tree_out.write(output_nav, encoding="utf-8", xml_declaration=False)

    return output_nav


if __name__ == "__main__":
    dtbook_file = "./output/nguvan/DAISY/dtbook.xml"
    nav_file = export_navmap(dtbook_file, "toc.ncx")
    print(f"✅ Đã xuất file NAV: {nav_file}")
