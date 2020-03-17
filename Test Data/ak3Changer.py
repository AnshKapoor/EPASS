from lxml import etree
ak3tree = etree.parse('plate_old (copy).ak3')
root = ak3tree.getroot()

test1 = etree.SubElement(root, "test1")
test1.text='\n'
test1.tail='\n'
ID = etree.SubElement(test1, 'ID')
ID.text = "Dies ist ein test"
ID.tail = '\n'
test1.set("N", "123")
idtest = test1.find('ID')
idtest2 = etree.SubElement(idtest, 'LOL')
ak3tree.write('NEU')
