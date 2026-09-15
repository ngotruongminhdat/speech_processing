import json
import xml.etree.ElementTree as ET
import os

def generate_smil(xml_file, json_file, smil_file, audio_path):
    # ====== Đọc file JSON ======
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    segments = data.get("segments", [])

    # ====== Đọc file XML ======
    tree = ET.parse(xml_file)
    root = tree.getroot()
    ns = {"dtbook": "http://www.daisy.org/z3986/2005/dtbook/"}

    p_tags = root.findall(".//dtbook:level1/dtbook:p", ns)

    if len(p_tags) != len(segments):
        print(f"⚠️ Cảnh báo: số lượng <p> ({len(p_tags)}) và segments ({len(segments)}) không khớp!")

    # ====== Tạo cấu trúc SMIL ======
    smil_ns = "http://www.w3.org/2001/SMIL20/"
    ET.register_namespace("", smil_ns)
    smil_root = ET.Element("smil", xmlns=smil_ns)

    # ====== HEAD ======
    head = ET.SubElement(smil_root, "head")
    ET.SubElement(head, "meta", {"content": "AUTO-UID-123456789", "name": "dtb:uid"})
    ET.SubElement(head, "meta", {"content": "0:00:00", "name": "dtb:totalElapsedTime"})
    ET.SubElement(head, "meta", {"content": "Python Script", "name": "dtb:generator"})

    custom_attr = ET.SubElement(head, "customAttributes")
    for attr in ["pagenum", "note", "noteref", "annotation", "linenum", "sidebar", "prodnote"]:
        ET.SubElement(custom_attr, "customTest", {"defaultState": "false", "id": attr, "override": "visible"})

    # ====== BODY ======
    body = ET.SubElement(smil_root, "body")
    root_seq = ET.SubElement(body, "seq", {"id": "root-seq"})

    for idx, (p_tag, seg) in enumerate(zip(p_tags, segments), 1):
        # Lấy <sent> bên trong <p>
        sent_tag = p_tag.find("dtbook:sent", ns)
        if sent_tag is None:
            print(f"⚠️ Không tìm thấy <sent> trong <p id={p_tag.attrib.get('id')}>")
            continue

        sent_id = sent_tag.attrib["id"]  # vd: id_4
        par_id = sent_id.replace("id_", "sid_")  # đổi thành sid_4

        seq = ET.SubElement(root_seq, "seq", {"id": f"seq_{idx}", "class": "p"})
        par = ET.SubElement(seq, "par", {"id": par_id, "class": "sent"})

        # textref trỏ đến <sent>
        ET.SubElement(
            par,
            "text",
            {"src": f"dtbook.xml#{sent_id}"}
        )

        # audio clip
        ET.SubElement(
            par,
            "audio",
            {
                "src": audio_path,
                "clipBegin": f"{seg['start']:.3f}s",
                "clipEnd": f"{seg['end']:.3f}s"
            }
        )

    # ====== Ghi ra file SMIL ======
    smil_tree = ET.ElementTree(smil_root)
    with open(smil_file, "wb") as f:
        f.write(b'<?xml version="1.0" encoding="utf-8"?>\n')
        f.write(b'<!DOCTYPE smil PUBLIC "-//NISO//DTD dtbsmil 2005-2//EN" "http://www.daisy.org/z3986/2005/dtbsmil-2005-2.dtd">\n')
        smil_tree.write(f, encoding="utf-8")

    print(f"✅ Đã tạo file {smil_file} thành công!")
