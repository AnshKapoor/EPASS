from lxml import etree
ak3tree = etree.parse('plate_old (copy).ak3')
root = ak3tree.getroot()
# elements = etree.SubElement(root, 'elements').text = 'pass'
# eltype = etree.SubElement(elements, 'type').text = 'lol'
newLoadedElem = ak3tree.Element('LALALAA')
newLoadedElem.tail = '\n'
newElemID = ak3tree.Element('XD')
newLoadedElem.append(newElemID)
ak3tree.write('NEU')
