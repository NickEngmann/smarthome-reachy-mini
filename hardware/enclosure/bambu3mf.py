#!/usr/bin/env python3
"""Bambu Studio project (.3mf) writer: bambu_v2.py writes the v2 enclosure's projects with it.
(Carried over from the reMixTape enclosure, where enclosure_v2.py and mold.py use it.)

A project holds objects; an object holds parts (bodies), each on a filament; a plate
lays the objects out; the printer, process and filament settings ride along in
Metadata/project_settings.config. write_project() takes cadquery shapes already in
print orientation and writes the package the way Bambu Studio 02.07 does, with an
`extruder` entry on every part - that is what puts a body on a filament.

Settings start from a project saved on the target machine
(bambu/project_settings.json: X1 Carbon, 0.4 mm nozzle, "0.20mm Standard", Bambu PLA
Basic) and are transformed: with_filament() puts a Bambu filament preset in, filaments()
makes it several, process() sets the process values; a part's own values ride along as
object settings (objects[i]["settings"]), which the slicer applies over the process. Bambu Studio's own filament
profiles (resources/profiles/BBL/filament, inheritance resolved) supply a real PETG
profile when the slicer is installed; without it the reference filament stays and a
note is printed. A project written here was checked by slicing it with the slicer's
own command line (bambu-studio.exe --slice 0 --export-3mf x.3mf --outputdir d in.3mf).
"""
import datetime, json, os, uuid, zipfile
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REFERENCE = os.path.join(HERE, "bambu", "project_settings.json")
BS_VERSION = "02.07.01.62"                                             # the Bambu Studio that wrote the reference project
BS_PROFILES = r"C:\Program Files\Bambu Studio\resources\profiles\BBL\filament"

# Bambu Studio keeps one block of values per filament in these vectors (a block is one value,
# or one per extruder variant). Names not starting with filament_ that its own filament
# profiles set (resources/profiles/BBL/filament/*.json, 2.07): a second filament repeats the block.
NONPREFIX_FILAMENT_KEYS = set("""
activate_air_filtration additional_cooling_fan_speed additional_fan_full_speed_layer chamber_temperatures
circle_compensation_speed close_additional_fan_first_x_layers close_fan_the_first_x_layers
complete_print_exhaust_fan_speed cool_plate_temp cool_plate_temp_initial_layer cooling_perimeter_transition_distance
cooling_slowdown_logic counter_coef_1 counter_coef_2 counter_coef_3 counter_limit_max counter_limit_min diameter_limit
during_print_exhaust_fan_speed eng_plate_temp eng_plate_temp_initial_layer fan_cooling_layer_time fan_max_speed
fan_min_speed first_x_layer_fan_speed full_fan_speed_layer hole_coef_1 hole_coef_2 hole_coef_3 hole_limit_max
hole_limit_min hot_plate_temp hot_plate_temp_initial_layer impact_strength_z long_retractions_when_ec
no_slow_down_for_cooling_on_outwalls nozzle_temperature nozzle_temperature_initial_layer nozzle_temperature_range_high
nozzle_temperature_range_low overhang_fan_speed overhang_fan_threshold override_process_overhang_speed pre_start_fan_time
reduce_fan_stop_start_freq required_nozzle_HRC retraction_distances_when_ec slow_down_for_layer_cooling
slow_down_layer_time slow_down_min_speed supertack_plate_temp supertack_plate_temp_initial_layer temperature_vitrification
textured_plate_temp textured_plate_temp_initial_layer volumetric_speed_coefficients flush_volumes_vector
""".split())
META_KEYS = {"name", "inherits", "type", "from", "instantiation", "setting_id", "version", "is_custom_defined",
             "description", "filament_vendor", "compatible_printers", "compatible_printers_condition",
             "compatible_prints", "compatible_prints_condition", "filament_id"}

def is_filament_key(k):
    return k.startswith("filament_") or k in NONPREFIX_FILAMENT_KEYS

def load_reference():
    """The reference project's settings, or None when the file is not there."""
    return json.load(open(REFERENCE, encoding="utf-8")) if os.path.exists(REFERENCE) else None

# ------------------------------------------------------------ settings transforms
def two_filaments(ps, accent_colour="#FFFFFF", flush_mm3="400"):
    """The reference single-filament project settings as a two-filament project: filament 2 is
    a copy of filament 1 (the real one is picked in the slicer), previewed in accent_colour;
    flush_mm3 both ways in the flush matrix (raw; the profile's multiplier applies)."""
    ps = dict(ps)
    if len(ps.get("filament_settings_id", [None])) != 1:
        return ps
    for k, v in list(ps.items()):
        if isinstance(v, list) and v and is_filament_key(k):
            ps[k] = v + v
    if "filament_self_index" in ps:                                    # which filament each block belongs to
        n = len(ps["filament_self_index"]) // 2
        ps["filament_self_index"] = ["1"] * n + ["2"] * n
    ps["filament_colour"] = [ps["filament_colour"][0], accent_colour]
    ps["flush_volumes_matrix"] = ["0", flush_mm3, flush_mm3, "0"]
    for k in ("different_settings_to_system", "inherits_group"):     # print, filament(s), printer
        if k in ps and len(ps[k]) == 3:
            v = ps[k]
            ps[k] = [v[0], v[1], v[1], v[2]]
    return ps

def filaments(ps, colours, flush_mm3="400"):
    """two_filaments() for any number: len(colours) copies of the reference's filament,
    previewed in those colours, flush_mm3 between every pair."""
    ps = dict(ps)
    n = len(colours)
    if len(ps.get("filament_settings_id", [None])) != 1 or n < 2:
        return ps
    for k, v in list(ps.items()):
        if isinstance(v, list) and v and is_filament_key(k):
            ps[k] = v * n
    if "filament_self_index" in ps:
        m = len(ps["filament_self_index"]) // n
        ps["filament_self_index"] = [str(i + 1) for i in range(n) for _ in range(m)]
    ps["filament_colour"] = list(colours)
    ps["flush_volumes_matrix"] = ["0" if i == j else flush_mm3 for i in range(n) for j in range(n)]
    for k in ("different_settings_to_system", "inherits_group"):     # print, filament(s), printer
        if k in ps and len(ps[k]) == 3:
            v = ps[k]
            ps[k] = [v[0]] + [v[1]] * n + [v[2]]
    return ps

def process(ps, name, **kv):
    """The reference process with these values set (strings, as Bambu Studio stores them; a
    vector setting gets the value in every slot), recorded as changed from the system preset
    and named after the project."""
    ps = dict(ps)
    for k, v in kv.items():
        ps[k] = [str(v)] * len(ps[k]) if isinstance(ps.get(k), list) else str(v)
    ps["print_settings_id"] = "%s - %s" % (ps.get("print_settings_id", "0.20mm Standard @BBL X1C").split(" - ")[0], name)
    if ps.get("different_settings_to_system"):
        d = list(ps["different_settings_to_system"])
        d[0] = ";".join(sorted(set((d[0] + ";" + ";".join(kv)).strip(";").split(";"))))
        ps["different_settings_to_system"] = d
    return ps

def filament_preset(name):
    """A Bambu filament profile with its inheritance chain resolved (child over parent), or
    None when the slicer's profiles are not on this machine."""
    chain = []
    while name:
        p = os.path.join(BS_PROFILES, name + ".json")
        if not os.path.exists(p):
            return None
        j = json.load(open(p, encoding="utf-8"))
        chain.append(j)
        name = j.get("inherits")
    merged = {}
    for j in reversed(chain):
        merged.update(j)
    return merged

def with_filament(ps, preset="Bambu PETG Basic @BBL X1C", colour="#8E9089"):
    """The reference settings with their (single) filament replaced by a Bambu preset: every
    key the preset chain sets is written over the reference's, a one-value vector repeated to
    the reference's length (one block per extruder variant); the preset's id and name go in
    filament_ids / filament_settings_id. Keys the chain does not set keep the reference's."""
    ps = dict(ps)
    pre = filament_preset(preset)
    if pre is None:
        print("bambu3mf: '%s' not found under %s - the reference filament (%s) stays" % (preset, BS_PROFILES, ps.get("filament_settings_id")))
        return ps
    n = len(ps.get("filament_settings_id", [None]))
    for k, v in pre.items():
        if k in META_KEYS:
            continue
        if isinstance(v, list):
            have = ps.get(k)
            if isinstance(have, list) and len(have) != len(v) and len(v) == 1:
                ps[k] = list(v) * len(have)
            else:
                ps[k] = list(v)
        else:
            ps[k] = v
    ps["filament_settings_id"] = [preset] * n
    ps["filament_ids"] = [pre.get("filament_id", "")] * n
    ps["filament_colour"] = [colour] * n
    for k in ("different_settings_to_system",):                        # the filament is a system preset, untouched
        if k in ps and len(ps[k]) >= 2:
            v = list(ps[k]); v[1] = ""; ps[k] = v
    return ps

def mold_process(ps, walls=4, top=6, bottom=6, infill="25%", pattern="gyroid", outer_wall_speed="100", ironing=False):
    """The process for a mould block: solid where it matters (walls, top and bottom shells),
    gyroid inside, no supports (every cavity overhang is a chamfer or a short bridge), the
    outer wall slowed - the cavity surface is the part's surface - and no ironing. Measured on
    the tray set (X1C, 0.2 mm): 5 walls / 35 % / ironing 9 h 01; without ironing 8 h 17;
    4 walls / 25 % 7 h 23 (260 g); 0.28 mm layers would give 6 h 34 at a coarser cavity."""
    ps = dict(ps)
    n = len(ps.get("outer_wall_speed", ["0"])) if isinstance(ps.get("outer_wall_speed"), list) else 1
    ps["wall_loops"] = str(walls)
    ps["top_shell_layers"] = str(top)
    ps["bottom_shell_layers"] = str(bottom)
    ps["sparse_infill_density"] = infill
    ps["sparse_infill_pattern"] = pattern
    ps["enable_support"] = "0"
    if not ironing:
        ps["ironing_type"] = "no ironing"                             # 44 min on the tray set; the parting faces get sanded flat anyway
    ps["outer_wall_speed"] = [outer_wall_speed] * n
    ps["print_settings_id"] = ps.get("print_settings_id", "0.20mm Standard") + " - reMixTape moulds"
    changed = "wall_loops;top_shell_layers;bottom_shell_layers;sparse_infill_density;sparse_infill_pattern;enable_support;outer_wall_speed;ironing_type"
    if "different_settings_to_system" in ps and ps["different_settings_to_system"]:
        d = list(ps["different_settings_to_system"])
        d[0] = ";".join(sorted(set((d[0] + ";" + changed).strip(";").split(";"))))
        ps["different_settings_to_system"] = d
    return ps

# ------------------------------------------------------------------- the package
def tessellate(shape, tol=0.02, ang=0.1):
    v, t = shape.val().tessellate(tol, ang)
    return np.array([[p.x, p.y, p.z] for p in v], dtype=float), np.array(t, dtype=int)

def write_project(path, objects, settings, title):
    """objects: [dict(name, parts=[dict(name, shape, extruder, tol?)], at=[(x, y), ...])] - shapes in
    print orientation, one container object per `at` entry (instances share the meshes), each
    centred on its bounding box and set down on the plate at (x, y). settings: the
    project_settings dict, or None for a project that takes the slicer's current presets."""
    objs = []
    for ob in objects:
        meshes = []
        for p in ob["parts"]:
            V, T = p["mesh"] if "mesh" in p else tessellate(p["shape"], p.get("tol", 0.02), 0.1)
            meshes.append(dict(name=p["name"], V=V, T=T, extruder=p.get("extruder", 1)))
        allV = np.concatenate([m["V"] for m in meshes])
        mn, mx = allV.min(0), allV.max(0)
        objs.append(dict(name=ob["name"], meshes=meshes, centre=(mn + mx) / 2, height=mx[2] - mn[2], at=ob["at"],
                         settings=ob.get("settings", {})))
    n_fil = len(settings["filament_settings_id"]) if settings and isinstance(settings.get("filament_settings_id"), list) else 1
    NS = ('xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02" '
          'xmlns:BambuStudio="http://schemas.bambulab.com/package/2021" '
          'xmlns:p="http://schemas.microsoft.com/3dmanufacturing/production/2015/06" requiredextensions="p"')
    files, rels, resources, build, cfg, plate = {}, [], [], [], [], []
    nid, ident = 1, 100
    for k, ob in enumerate(objs, 1):
        fname = "3D/Objects/object_%d.model" % k
        xml = ['<?xml version="1.0" encoding="UTF-8"?>', '<model unit="millimeter" xml:lang="en-US" %s>' % NS,
               ' <metadata name="BambuStudio:3mfVersion">1</metadata>', ' <resources>']
        c = ob["centre"]
        for m in ob["meshes"]:
            m["id"] = nid
            nid += 1
            xml.append('  <object id="%d" p:UUID="%s" type="model">\n   <mesh>\n    <vertices>' % (m["id"], uuid.uuid4()))
            xml.extend('     <vertex x="%.5f" y="%.5f" z="%.5f"/>' % (x - c[0], y - c[1], z - c[2]) for x, y, z in m["V"])
            xml.append('    </vertices>\n    <triangles>')
            xml.extend('     <triangle v1="%d" v2="%d" v3="%d"/>' % (a, b, d) for a, b, d in m["T"])
            xml.append('    </triangles>\n   </mesh>\n  </object>')
        xml.append(' </resources>\n <build/>\n</model>')
        files[fname] = "\n".join(xml)
        rels.append(' <Relationship Target="/%s" Id="rel-%d" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>' % (fname, k))
        for (px, py) in ob["at"]:                                     # one container object per instance, sharing the meshes
            cid = nid
            nid += 1
            resources.append('  <object id="%d" p:UUID="%s" type="model">\n   <components>' % (cid, uuid.uuid4()))
            for m in ob["meshes"]:
                resources.append('    <component p:path="/%s" objectid="%d" p:UUID="%s" transform="1 0 0 0 1 0 0 0 1 0 0 0"/>' % (fname, m["id"], uuid.uuid4()))
            resources.append('   </components>\n  </object>')
            build.append('  <item objectid="%d" p:UUID="%s" transform="1 0 0 0 1 0 0 0 1 %.4f %.4f %.4f" printable="1"/>' % (cid, uuid.uuid4(), px, py, ob["height"] / 2))
            cfg.append('  <object id="%d">\n    <metadata key="name" value="%s"/>\n    <metadata key="extruder" value="1"/>\n    <metadata face_count="%d"/>'
                       % (cid, ob["name"], sum(len(m["T"]) for m in ob["meshes"])))
            for k, v in ob["settings"].items():                      # the part's own process values
                cfg.append('    <metadata key="%s" value="%s"/>' % (k, v))
            for m in ob["meshes"]:
                cfg.append('    <part id="%d" subtype="normal_part">\n      <metadata key="name" value="%s"/>\n      <metadata key="matrix" value="1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1"/>\n'
                           '      <metadata key="source_file" value="%s.stl"/>\n      <metadata key="source_object_id" value="0"/>\n      <metadata key="source_volume_id" value="0"/>\n'
                           '      <metadata key="source_offset_x" value="%.4f"/>\n      <metadata key="source_offset_y" value="%.4f"/>\n      <metadata key="source_offset_z" value="%.4f"/>\n'
                           '      <metadata key="extruder" value="%d"/>\n      <mesh_stat face_count="%d" edges_fixed="0" degenerate_facets="0" facets_removed="0" facets_reversed="0" backwards_edges="0"/>\n    </part>'
                           % (m["id"], m["name"], m["name"], c[0], c[1], c[2], m["extruder"], len(m["T"])))
            cfg.append('  </object>')
            plate.append('    <model_instance>\n      <metadata key="object_id" value="%d"/>\n      <metadata key="instance_id" value="0"/>\n      <metadata key="identify_id" value="%d"/>\n    </model_instance>' % (cid, ident))
            ident += 1
    today = datetime.date.today().isoformat()
    files["3D/3dmodel.model"] = "\n".join(
        ['<?xml version="1.0" encoding="UTF-8"?>', '<model unit="millimeter" xml:lang="en-US" %s>' % NS,
         ' <metadata name="Application">BambuStudio-%s</metadata>' % BS_VERSION, ' <metadata name="BambuStudio:3mfVersion">1</metadata>',
         ' <metadata name="CreationDate">%s</metadata>' % today, ' <metadata name="ModificationDate">%s</metadata>' % today,
         ' <metadata name="Title">%s</metadata>' % title, ' <resources>'] + resources +
        [' </resources>', ' <build p:UUID="%s">' % uuid.uuid4()] + build + [' </build>', '</model>'])
    files["3D/_rels/3dmodel.model.rels"] = "\n".join(['<?xml version="1.0" encoding="UTF-8"?>',
                                                       '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'] + rels + ['</Relationships>'])
    files["_rels/.rels"] = ('<?xml version="1.0" encoding="UTF-8"?>\n<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">\n'
                            ' <Relationship Target="/3D/3dmodel.model" Id="rel-1" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>\n</Relationships>')
    files["[Content_Types].xml"] = ('<?xml version="1.0" encoding="UTF-8"?>\n<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">\n'
                                    ' <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>\n'
                                    ' <Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>\n'
                                    ' <Default Extension="png" ContentType="image/png"/>\n <Default Extension="gcode" ContentType="text/x.gcode"/>\n</Types>')
    files["Metadata/model_settings.config"] = "\n".join(
        ['<?xml version="1.0" encoding="UTF-8"?>', '<config>'] + cfg +
        ['  <plate>', '    <metadata key="plater_id" value="1"/>', '    <metadata key="plater_name" value=""/>', '    <metadata key="locked" value="false"/>',
         '    <metadata key="filament_map_mode" value="Auto For Flush"/>',
         '    <metadata key="filament_maps" value="%s"/>' % " ".join(["1"] * n_fil),
         '    <metadata key="filament_volume_maps" value="%s"/>' % " ".join(["0"] * n_fil)] +
        plate + ['  </plate>', '</config>'])
    files["Metadata/slice_info.config"] = ('<?xml version="1.0" encoding="UTF-8"?>\n<config>\n  <header>\n    <header_item key="X-BBL-Client-Type" value="slicer"/>\n'
                                           '    <header_item key="X-BBL-Client-Version" value="%s"/>\n  </header>\n</config>' % BS_VERSION)
    if settings:
        files["Metadata/project_settings.config"] = json.dumps(settings, indent=4)
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        for n in ["[Content_Types].xml", "_rels/.rels", "3D/3dmodel.model", "3D/_rels/3dmodel.model.rels"] + \
                 sorted(n for n in files if n.startswith("3D/Objects")) + sorted(n for n in files if n.startswith("Metadata")):
            z.writestr(n, files[n])
    print("project written: %s (%d object%s, %d bodies%s)" % (path, len(objs), "" if len(objs) == 1 else "s",
          sum(len(o["meshes"]) for o in objs), "" if settings else ", no settings"))

def exclusion_x(settings):
    """How far the printer's front-left exclusion zone reaches in x (the X1 Carbon keeps
    an 18 x 28 mm corner for its nozzle wipe: bed_exclude_area, points as "18x28"). An object
    placed into it is an "object conflict" and the slicer refuses the plate before slicing."""
    pts = settings.get("bed_exclude_area") if settings else None
    if not pts:
        return 0.0
    try:
        return max(float(p.split("x")[0]) for p in pts)
    except (ValueError, AttributeError):
        return 0.0

def layout(rows, settings=None, gap=8.0, bed=256.0):
    """Set each object's `at` from its footprint: objects left to right in rows, rows front to
    back, `gap` apart, starting just past the printer's exclusion corner (x) and `gap` from
    the front (y). Single-instance objects. Raises if a row or the stack runs off the bed."""
    x0, y0 = exclusion_x(settings) + 4.0, gap
    y = y0
    for row in rows:
        x, h = x0, 0.0
        for ob in row:
            allV = np.concatenate([p["mesh"][0] if "mesh" in p else tessellate(p["shape"], 0.5, 0.5)[0] for p in ob["parts"]])
            mn, mx = allV.min(0), allV.max(0)
            w, d = mx[0] - mn[0], mx[1] - mn[1]
            ob["at"] = [(x + w / 2, y + d / 2)]
            x += w + gap
            h = max(h, d)
        if x - gap > bed - 4:
            raise ValueError("a row of the plate runs to x = %.0f, past the %.0f mm bed" % (x - gap, bed))
        y += h + gap
    if y - gap > bed - 4:
        raise ValueError("the plate stacks to y = %.0f, past the %.0f mm bed" % (y - gap, bed))
    return [ob for row in rows for ob in row]
