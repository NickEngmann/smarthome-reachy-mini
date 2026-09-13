"""List named components of the CrowPanel P4 STEP with world bounding boxes."""
import sys
from OCP.STEPCAFControl import STEPCAFControl_Reader
from OCP.TDocStd import TDocStd_Document
from OCP.TCollection import TCollection_ExtendedString
from OCP.XCAFDoc import XCAFDoc_DocumentTool, XCAFDoc_ShapeTool
from OCP.TDF import TDF_LabelSequence, TDF_Label
from OCP.TDataStd import TDataStd_Name
from OCP.Bnd import Bnd_Box
from OCP.BRepBndLib import BRepBndLib
from OCP.IFSelect import IFSelect_RetDone

path = sys.argv[1]
doc = TDocStd_Document(TCollection_ExtendedString("doc"))
r = STEPCAFControl_Reader()
r.SetNameMode(True)
assert r.ReadFile(path) == IFSelect_RetDone
r.Transfer(doc)
st = XCAFDoc_DocumentTool.ShapeTool_s(doc.Main())


def name(lab):
    n = TDataStd_Name()
    if lab.FindAttribute(TDataStd_Name.GetID_s(), n):
        return n.Get().ToExtString()
    return "?"


rows = []
free = TDF_LabelSequence()
st.GetFreeShapes(free)
for i in range(1, free.Length() + 1):
    top = free.Value(i)
    comps = TDF_LabelSequence()
    XCAFDoc_ShapeTool.GetComponents_s(top, comps, True)
    for j in range(1, comps.Length() + 1):
        c = comps.Value(j)
        ref = TDF_Label()
        refname = name(c)
        if XCAFDoc_ShapeTool.GetReferredShape_s(c, ref):
            if XCAFDoc_ShapeTool.IsAssembly_s(ref):
                continue
            refname = f"{name(c)} -> {name(ref)}"
        shp = XCAFDoc_ShapeTool.GetShape_s(c)
        if shp.IsNull():
            continue
        b = Bnd_Box()
        BRepBndLib.Add_s(shp, b)
        if b.IsVoid():
            continue
        x0, y0, z0, x1, y1, z1 = b.Get()
        rows.append((refname, x0, y0, z0, x1, y1, z1))

for n, x0, y0, z0, x1, y1, z1 in sorted(rows, key=lambda r: (r[3], r[1])):
    print(f"{n[:60]:60s} size {x1-x0:7.2f} x {y1-y0:6.2f} x {z1-z0:7.2f}  x[{x0:7.2f},{x1:7.2f}] y[{y0:6.2f},{y1:6.2f}] z[{z0:7.2f},{z1:7.2f}]")
print(len(rows), "components")
