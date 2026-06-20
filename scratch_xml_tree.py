import xml.etree.ElementTree as ET

tree = ET.parse("scratch/meta_test.lsx")
root = tree.getroot()
print(root.tag)  # what is the root element?
print(root.attrib)  # what attributes does it have?

for child in root:
    print(child.tag, child.attrib)
    for grandchild in child:
        print("  ", grandchild.tag, grandchild.attrib)
