#!/usr/bin/env python
"""
gh_params_gen — GhPython whole-component generator
==================================================
Parse the docstring of a Rhino 8 Script-component script and emit a full
Grasshopper **clipboard archive** that, pasted onto the canvas, creates the
entire Python 3 Script component — the whole `.py` embedded as runnable code,
the input/output params (nicknames, access, type hints), each param's **tooltip**
(`(pytype) description` from the docstring), and the component's own description.
So a working, fully-documented component appears with one paste — nothing wired
by hand.

Source of truth is the docstring convention (see `context/gh-params-convention.md`):

    Inputs (Grasshopper):
        <nickname> : <pytype> @<access>[ optional|required][ hint=<Token>]
            <description — becomes the input's tooltip>

    Outputs (Grasshopper):
        <nickname> : <pytype>
            <description — becomes the output's tooltip>

`@item` / `@list` / `@tree` is mandatory on every input. Every recognised input
pytype auto-maps to a concrete TypeHintID — scalars (`float`/`int`/`str`/`bool`/
`complex`) to the matching .NET hint, geometry (`rg.Mesh`, `list[Point3d]`,
`Brep | None`) to its RhinoCommon hint; `hint=<Token>` overrides explicitly, and an
unrecognised core type (`dict`, `object`, `None`) falls back to "No conversion".
Outputs always stay "No conversion" (the Script component's only output hint). The
component's tooltip comes from the docstring `Purpose:` block; the standard `out`
stdout param is always added as the first output.

Pure stdlib (no Rhino / numpy / third-party deps) so it runs under any
interpreter and inside the regen hooks. CPython 3.8+.

CLI:
    python tools/gh_params_gen.py <script.py> [--out PATH] [--stdout]
           [--clipboard] [--fresh-guids] [--check] [--quiet]

Author:   Aleksander Mastalski / gh_scripts
"""

from __future__ import annotations

import argparse
import ast
import base64
import hashlib
import os
import re
import subprocess
import sys
import uuid
from dataclasses import dataclass, field
from xml.sax.saxutils import escape as _xml_escape


# ---------------------------------------------------------------------------
# Hint registry (extracted from the Rhino 8 sampler paste — see
# tests/fixtures/sampler_38_inputs.xml). Each hint contributes three fields to
# a generated param: Description, TypeHintID, and ConverterData (assembly+type).
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class HintInfo:
    description: str
    type_hint_id: str
    converter_assembly: str
    converter_type: str


NO_CONVERSION = HintInfo(
    "No conversion",
    "6a184b65-baa3-42d1-a548-3915b401de53",
    "System.Private.CoreLib",
    "System.Object",
)

# (canonical token, [aliases], HintInfo). Tokens are matched case-insensitively.
_HINT_ROWS = [
    ("ghdoc_object", ["ghdoc", "rhinoscriptsyntax"],
     HintInfo("rhinoscriptsyntax geometry", "1c282eeb-dd16-439f-94e4-7d92b542fe8b",
              "System.Private.CoreLib", "System.Object")),
    ("bool", ["boolean"],
     HintInfo("Converts to collection of boolean values", "d60527f5-b5af-4ef6-8970-5f96fe412559",
              "System.Private.CoreLib", "System.Boolean")),
    ("int", ["integer"],
     HintInfo("Converts to collection of integer numbers", "48d01794-d3d8-4aef-990e-127168822244",
              "System.Private.CoreLib", "System.Int32")),
    ("str", ["string", "text"],
     HintInfo("Converts to collection of text fragments", "3aceb454-6dbd-4c5b-9b6b-e71f8c1cdf88",
              "System.Private.CoreLib", "System.String")),
    ("float", ["double", "number"],
     HintInfo("Converts to collection of floating point numbers", "9d51e32e-c038-4352-9554-f4137ca91b9a",
              "System.Private.CoreLib", "System.Double")),
    ("complex", [],
     HintInfo("Converts to collection of complex numbers", "309690df-6229-4774-91bb-b1c9c0bfa54d",
              "System.Runtime.Numerics", "System.Numerics.Complex")),
    ("datetime", ["date"],
     HintInfo("Converts to collection of date time format strings", "09bcf900-fe83-4efa-8d32-33d89f7a3e66",
              "System.Private.CoreLib", "System.DateTime")),
    ("color", ["system_drawing_color", "colour"],
     HintInfo("Converts to collection of RGB colours", "24b1d1a3-ab79-498c-9e44-c5b14607c4d3",
              "System.Drawing.Primitives", "System.Drawing.Color")),
    ("filepath", ["file_path"],
     HintInfo("Converts to collection of file paths. Ensures paths are absolute based on document location",
              "d969c421-cd3c-43f3-aef0-abad97d6526a", "System.Private.CoreLib", "System.String")),
    ("point3d", ["point"],
     HintInfo("Converts to collection of three-dimensional points", "e1937b56-b1da-4c12-8bd8-e34ee81746ef",
              "RhinoCommon", "Rhino.Geometry.Point3d")),
    ("point3dlist", [],
     HintInfo("Converts to collection of three-dimensional points.\n"
              "Primarily to convert Polyline into list of points to match legacy GHPython behaviour.\n"
              "This is only supported in Rhino >= 8.7",
              "b2ea84da-7a94-4144-9f7a-63167abd77e3", "RhinoCommon", "Rhino.Collections.Point3dList")),
    ("vector3d", ["vector"],
     HintInfo("Converts to collection of three-dimensional vectors", "15a50725-e3d3-4075-9f7c-142ba5f40747",
              "RhinoCommon", "Rhino.Geometry.Vector3d")),
    ("plane", [],
     HintInfo("Converts to collection of three-dimensional axis-systems", "3897522d-58e9-4d60-b38c-978ddacfedd8",
              "RhinoCommon", "Rhino.Geometry.Plane")),
    ("interval", ["interval_domain", "domain"],
     HintInfo("Converts to collection of numeric domains", "589748aa-e558-4dd9-976f-78e3ab91fc77",
              "RhinoCommon", "Rhino.Geometry.Interval")),
    ("uvinterval", ["uvinterval_domain2d", "domain2d"],
     HintInfo("Converts to collection of 2D number domains", "74c906f3-db02-4cea-bd58-de375cb5ae73",
              "Grasshopper", "Grasshopper.Kernel.Types.UVInterval")),
    ("guid", ["uuid"],
     HintInfo("Converts to collection of Globally Unique Identifiers", "5325b8e1-51d7-4d36-837a-d98394626c35",
              "System.Private.CoreLib", "System.Guid")),
    ("box", [],
     HintInfo("Converts to collection of boxes", "f29cb021-de79-4e63-9f04-fc8e0df5f8b6",
              "RhinoCommon", "Rhino.Geometry.Box")),
    ("transform", ["xform"],
     HintInfo("Converts to collection of three-dimensional transformations", "c4b38e4c-21ff-415f-a0d1-406d282428dd",
              "RhinoCommon", "Rhino.Geometry.Transform")),
    ("line", [],
     HintInfo("Converts to collection of line segments", "f802a8cd-e699-4a94-97ea-83b5406271de",
              "RhinoCommon", "Rhino.Geometry.Line")),
    ("circle", [],
     HintInfo("Converts to collection of circles", "3c5409a1-3293-4181-a6fa-c24c37fc0c32",
              "RhinoCommon", "Rhino.Geometry.Circle")),
    ("arc", [],
     HintInfo("Converts to collection of circular arcs", "9c80ec18-b48c-41b0-bc6e-cd93d9c916aa",
              "RhinoCommon", "Rhino.Geometry.Arc")),
    ("curve", [],
     HintInfo("Converts to collection of generic curves", "9ba89ec2-5315-435f-a621-b66c5fa2f301",
              "RhinoCommon", "Rhino.Geometry.Curve")),
    ("polyline", [],
     HintInfo("Converts to collection of generic curves", "66fa617b-e3e8-4480-9f1e-2c0688c1d21b",
              "RhinoCommon", "Rhino.Geometry.Polyline")),
    ("rectangle3d", ["rectangle", "rect"],
     HintInfo("Converts to collection of rectangles", "83da014b-a550-4bf5-89ff-16e54225bd5d",
              "RhinoCommon", "Rhino.Geometry.Rectangle3d")),
    ("mesh", [],
     HintInfo("Converts to collection of polygon meshes", "794a1f9d-21d5-4379-b987-9e8bbf433912",
              "RhinoCommon", "Rhino.Geometry.Mesh")),
    ("surface", ["srf"],
     HintInfo("Converts to collection of generic surfaces", "f4070a37-c822-410f-9057-100d2e22a22d",
              "RhinoCommon", "Rhino.Geometry.Surface")),
    ("extrusion", [],
     HintInfo("Converts to collection of Extrusions", "55816132-8684-4462-9786-df5a0e165430",
              "RhinoCommon", "Rhino.Geometry.Extrusion")),
    ("subd", [],
     HintInfo("Converts to collection of SubDs", "20f4ca9c-6c90-4fd6-ba8a-5bf9ca79db08",
              "RhinoCommon", "Rhino.Geometry.SubD")),
    ("brep", [],
     HintInfo("Converts to collection of Breps (Boundary REPresentations)", "2ceb0405-fdfe-403d-a4d6-8786da45fb9d",
              "RhinoCommon", "Rhino.Geometry.Brep")),
    ("pointcloud", [],
     HintInfo("Converts to collection of point clouds", "d73c9fb0-365d-458f-9fb5-f4141399311f",
              "RhinoCommon", "Rhino.Geometry.PointCloud")),
    ("geometrybase", ["geometry"],
     HintInfo("Converts to collection of generic geometry", "c37956f4-d39c-49c7-af71-1e87f8031b26",
              "RhinoCommon", "Rhino.Geometry.GeometryBase")),
    ("hatch", [],
     HintInfo("Converts to collection of hatches", "4565f2a4-3fd1-4b53-b47b-54aee8e3732e",
              "RhinoCommon", "Rhino.Geometry.Hatch")),
    ("leader", [],
     HintInfo("Converts to collection of leaders", "23d3f942-a6c7-40e1-86d5-33ef632a6a86",
              "RhinoCommon", "Rhino.Geometry.Leader")),
]

# token -> HintInfo, including aliases and the No-conversion fallbacks.
HINTS = {"object": NO_CONVERSION, "none": NO_CONVERSION,
         "noconversion": NO_CONVERSION, "textdot": NO_CONVERSION,
         "textentity": NO_CONVERSION}
for _canon, _aliases, _info in _HINT_ROWS:
    for _tok in [_canon] + list(_aliases):
        HINTS[_tok] = _info

# Fixed project namespace for deterministic uuid5 InstanceGuids. Do not change
# it once sidecars are committed, or every GUID churns.
_NAMESPACE = uuid.UUID("6f9b1c2d-3e4a-5b6c-7d8e-9f0a1b2c3d4e")

_ACCESS = {"item": 0, "list": 1, "tree": 2}

# --- Component-archive GUIDs (reverse-engineered from a real Rhino 8 paste;
# see tests/fixtures/component_minimal.xml) ---------------------------------
COMPONENT_GUID = "719467e6-7cf5-4848-99b0-c5dd57e5442c"      # "Python 3 Script" component type
SCRIPT_VAR_PARAM = "08908df5-fa14-4982-9ab2-1aa0927566aa"    # script-variable param (in + user out)
STANDARD_OUT_PARAM = "3ede854e-c753-40eb-84cb-b48008f14fd4"  # the always-first stdout "out" param
_STANDARD_OUT_DESC = "Standard output and error contents collected during script run"
# Grasshopper core library declaration (verbatim from the paste).
_GH_LIB = {"Author": "Robert McNeel & Associates",
           "Id": "00000000-0000-0000-0000-000000000000",
           "Name": "Grasshopper", "Version": "8.27.26019.16021"}
_PLUGIN_VERSION = (1, 0, 8)
_ARCHIVE_VERSION = (0, 2, 2)
_DATE_TICKS = "639160225397381479"  # cosmetic gh_date (a fixed .NET ticks value)

_SECTION_HDR = re.compile(r"^(Inputs|Outputs)\b[^\n]*\(Grasshopper[^)]*\)[^\n]*:\s*$")
_PURPOSE_HDR = re.compile(r"^Purpose\s*:\s*$")
_NAME_LIST = r"[A-Za-z_]\w*(?:\s*,\s*[A-Za-z_]\w*)*"
_PARAM_LINE = re.compile(r"^(" + _NAME_LIST + r")\s*(?::\s*(.*))?$")
_ACCESS_SENTENCE = re.compile(r"\s*\b(Item|List|Tree)\s+access\.?\s*$")


class ParamConventionError(ValueError):
    """Raised when a docstring violates the @-tag convention."""


@dataclass
class ParamSpec:
    nickname: str
    pytype: str
    kind: str            # "in" | "out"
    access: int = 0      # 0 item / 1 list / 2 tree
    optional: bool = True
    hint: HintInfo = NO_CONVERSION
    description: str = ""  # human tooltip text from the docstring


@dataclass
class ParseResult:
    inputs: list  # list[ParamSpec]
    outputs: list
    has_sections: bool
    warnings: list = field(default_factory=list)
    component_desc: str = ""  # docstring Purpose: → component tooltip


# ---------------------------------------------------------------------------
# Hint resolution
# ---------------------------------------------------------------------------
def _normalize_token(tok: str) -> str:
    return tok.strip().lower()


def _core_type(pytype: str) -> str:
    """Reduce a `pytype` annotation to its single core type identifier.

    `rg.Mesh` -> "Mesh"; `list[Point3d]` -> "Point3d"; `Brep | None` -> "Brep";
    `Rhino.Geometry.Curve` -> "Curve"; `list[float]` -> "float";
    `int | list[int]` -> "int" (every alternative reduces to one core type).

    A genuinely mixed annotation (`dict[str, float]`, `str | float`) has more than
    one distinct core, so it returns "" and falls back to No conversion rather than
    silently auto-mapping to whichever type happens to come last.
    """
    s = pytype or ""
    # drop single-arg container wrappers, keeping the element type inside the brackets
    s = re.sub(r"\b(Optional|List|list|Sequence|Iterable|Tuple|tuple|Set|set|frozenset|IEnumerable)\b",
               " ", s)
    s = s.replace("|", " ").replace("[", " ").replace("]", " ").replace(",", " ")
    tokens = [t for t in re.findall(r"[A-Za-z_][A-Za-z0-9_.]*", s) if t != "None"]
    # reduce each token to its final dotted component; exactly one distinct core auto-maps
    cores = {t.split(".")[-1] for t in tokens}
    if len(cores) != 1:
        return ""
    return next(iter(cores))


def resolve_hint(pytype: str, explicit=None, warnings=None) -> HintInfo:
    """Resolve a GH type hint per the convention (explicit → pytype auto-map → default).

    Every recognised pytype auto-maps to a concrete hint so inputs carry a real
    TypeHintID: scalars (`float`/`int`/`str`/`bool`/`complex`) to their matching .NET
    hint, geometry to its RhinoCommon hint. Only an empty or unrecognised core type
    (`dict`, `object`, `None`) falls back to No conversion. (Outputs are emitted as
    No conversion regardless — that is the Script component's only output hint.)
    """
    if explicit:
        key = _normalize_token(explicit)
        if key in HINTS:
            return HINTS[key]
        if warnings is not None:
            warnings.append(
                "unknown hint token '%s'; using No conversion. Valid: %s"
                % (explicit, ", ".join(sorted({r[0] for r in _HINT_ROWS}))))
        return NO_CONVERSION
    core = _normalize_token(_core_type(pytype))
    if not core:
        return NO_CONVERSION
    return HINTS.get(core, NO_CONVERSION)


# ---------------------------------------------------------------------------
# Docstring parsing
# ---------------------------------------------------------------------------
def _module_docstring(src_text: str) -> str:
    try:
        mod = ast.parse(src_text)
    except SyntaxError as ex:
        raise ParamConventionError("cannot parse script (%s)" % ex)
    return ast.get_docstring(mod, clean=False) or ""


def _section_bodies(lines):
    """Return {'Inputs': [body lines] | None, 'Outputs': ...}.

    A section spans from its header to the next non-indented, non-blank line.
    """
    out = {"Inputs": None, "Outputs": None}
    i, n = 0, len(lines)
    while i < n:
        m = _SECTION_HDR.match(lines[i])
        if not m:
            i += 1
            continue
        kind, body, j = m.group(1), [], i + 1
        while j < n and (lines[j].strip() == "" or lines[j][:1] in (" ", "\t")):
            body.append(lines[j])
            j += 1
        out[kind] = body
        i = j
    return out


def _base_indent(body):
    indents = [len(ln) - len(ln.lstrip()) for ln in body if ln.strip()]
    return min(indents) if indents else 0


def _collapse_desc(parts):
    """Join description fragments into one whitespace-collapsed tooltip line.

    Drops a trailing redundant "Item/List/Tree access." sentence (now carried
    by the @-tag).
    """
    text = " ".join(p.strip() for p in parts if p and p.strip())
    text = re.sub(r"\s+", " ", text).strip()
    return _ACCESS_SENTENCE.sub("", text).strip()


def _param_entries(body):
    """[(match, [description lines]), ...] — one per base-indent param line.

    Deeper-indented lines below a param line are collected as its description.
    """
    base = _base_indent(body)
    entries, cur = [], None
    for raw in body:
        if not raw.strip():
            continue
        indent = len(raw) - len(raw.lstrip())
        if indent == base:
            m = _PARAM_LINE.match(raw.strip())
            if m:
                cur = [m, []]
                entries.append(cur)
                continue
        if cur is not None:  # deeper / non-matching line → description of cur
            cur[1].append(raw.strip())
    return entries


def _tooltip(pytype, description):
    """`(pytype) description`, dropping either part when empty."""
    pytype = (pytype or "").strip()
    description = (description or "").strip()
    if pytype and description:
        return "(%s) %s" % (pytype, description)
    if pytype:
        return "(%s)" % pytype
    return description


def _parse_inputs(body, warnings):
    specs, seen = [], set()
    for m, desc_lines in _param_entries(body):
        names, rest = m.group(1), (m.group(2) or "")
        if "," in names:
            raise ParamConventionError(
                "input line declares multiple names (%s); one input per line" % names.strip())
        name = names.strip()
        if "@" not in rest:
            raise ParamConventionError(
                "input '%s' is missing its @item/@list/@tree access tag" % name)
        pytype, tag = rest.split("@", 1)
        parts = tag.split()
        if not parts or parts[0].lower() not in _ACCESS:
            raise ParamConventionError(
                "input '%s' has an invalid access tag '@%s' (use @item/@list/@tree)"
                % (name, tag.strip()))
        access = _ACCESS[parts[0].lower()]
        optional, hint_token = True, None
        for tp in parts[1:]:
            low = tp.lower()
            if low == "optional":
                optional = True
            elif low == "required":
                optional = False
            elif low.startswith("hint="):
                hint_token = tp.split("=", 1)[1]
            else:
                raise ParamConventionError(
                    "input '%s' has an unknown tag word '%s'" % (name, tp))
        if name in seen:
            raise ParamConventionError("duplicate input nickname '%s'" % name)
        seen.add(name)
        pytype = pytype.strip()
        specs.append(ParamSpec(name, pytype, "in", access, optional,
                               resolve_hint(pytype, hint_token, warnings),
                               _collapse_desc(desc_lines)))
    return specs


def _parse_outputs(body, warnings=None):
    specs, seen = [], set()
    for m, desc_lines in _param_entries(body):
        names, rest = m.group(1), (m.group(2) or "")
        # an em-dash on the param line starts an inline description
        if "—" in rest:
            pytype, inline = rest.split("—", 1)
        else:
            pytype, inline = rest, ""
        pytype = pytype.strip()
        desc = _collapse_desc([inline] + desc_lines)
        for name in (s.strip() for s in names.split(",")):
            if not name:
                continue
            if name in seen:
                raise ParamConventionError("duplicate output nickname '%s'" % name)
            seen.add(name)
            if not desc and warnings is not None:
                warnings.append(
                    "output '%s' has no tooltip prose (indented description "
                    "line under the param)" % name)
            specs.append(ParamSpec(name, pytype, "out", 0, False, NO_CONVERSION, desc))
    return specs


def _purpose(doc_lines):
    """The docstring `Purpose:` block, whitespace-collapsed (component tooltip)."""
    for i, line in enumerate(doc_lines):
        if _PURPOSE_HDR.match(line):
            body, j = [], i + 1
            while j < len(doc_lines) and (doc_lines[j].strip() == ""
                                          or doc_lines[j][:1] in (" ", "\t")):
                body.append(doc_lines[j])
                j += 1
            return _collapse_desc(body)
    return ""


def parse_docstring(src_text: str) -> ParseResult:
    """Parse a script's docstring into input/output ParamSpecs + component desc."""
    doc = _module_docstring(src_text)
    lines = doc.splitlines()
    bodies = _section_bodies(lines)
    has = bodies["Inputs"] is not None or bodies["Outputs"] is not None
    warnings = []
    inputs = _parse_inputs(bodies["Inputs"], warnings) if bodies["Inputs"] else []
    outputs = _parse_outputs(bodies["Outputs"], warnings) if bodies["Outputs"] else []
    if has and not re.search(r"^\s*Runtime:\s*$", doc, re.M):
        warnings.append("no Runtime: section in the docstring")
    return ParseResult(inputs, outputs, has, warnings, _purpose(lines))


# ---------------------------------------------------------------------------
# XML emitter — reproduces the sampler's CopiedParameters structure exactly
# ---------------------------------------------------------------------------
def _num(v) -> str:
    f = float(v)
    return str(int(f)) if f.is_integer() else repr(f)


def _instance_guid(relpath: str, section: str, nickname: str, fresh: bool) -> str:
    if fresh:
        return str(uuid.uuid4())
    return str(uuid.uuid5(_NAMESPACE, "%s:%s:%s" % (relpath, section, nickname)))


def _item(name, type_name, type_code, value, level):
    sp = "  " * level
    return ["%s<item name=\"%s\" type_name=\"%s\" type_code=\"%s\">%s</item>"
            % (sp, name, type_name, type_code, _xml_escape(str(value)))]


def _rect_item(name, x, y, w, h, level):
    sp, sp2 = "  " * level, "  " * (level + 1)
    return ["%s<item name=\"%s\" type_name=\"gh_drawing_rectanglef\" type_code=\"35\">" % (sp, name),
            "%s<X>%s</X>" % (sp2, _num(x)), "%s<Y>%s</Y>" % (sp2, _num(y)),
            "%s<W>%s</W>" % (sp2, _num(w)), "%s<H>%s</H>" % (sp2, _num(h)),
            "%s</item>" % sp]


def _point_item(name, x, y, level):
    sp, sp2 = "  " * level, "  " * (level + 1)
    return ["%s<item name=\"%s\" type_name=\"gh_drawing_pointf\" type_code=\"31\">" % (sp, name),
            "%s<X>%s</X>" % (sp2, _num(x)), "%s<Y>%s</Y>" % (sp2, _num(y)),
            "%s</item>" % sp]


def _bool(b: bool) -> str:
    return "true" if b else "false"


_AUTHOR_DEFAULT = "Aleksander Mastalski"


def _attr_chunk(x, y, w, h, level):
    """<chunk name="Attributes"> with Bounds / Pivot / Selected (param or component)."""
    L, L1 = "  " * level, "  " * (level + 1)
    out = ["%s<chunk name=\"Attributes\">" % L, "%s<items count=\"3\">" % L1]
    out += _rect_item("Bounds", x, y, w, h, level + 2)
    out += _point_item("Pivot", x + w / 2.0, y + h / 2.0, level + 2)
    out += _item("Selected", "gh_bool", "1", "true", level + 2)
    out += ["%s</items>" % L1, "%s</chunk>" % L]
    return out


def _converter_chunk(hint, level):
    L, L1 = "  " * level, "  " * (level + 1)
    out = ["%s<chunk name=\"ConverterData\">" % L, "%s<items count=\"2\">" % L1]
    out += _item("AssemblyName", "gh_string", "10", hint.converter_assembly, level + 2)
    out += _item("TypeName", "gh_string", "10", hint.converter_type, level + 2)
    out += ["%s</items>" % L1, "%s</chunk>" % L]
    return out


def _user_param_chunk(tag, index, p, guid, tooltip, x, y, level):
    """A 12-item user InputParam / OutputParam chunk (with hint + tooltip)."""
    is_input = p.kind == "in"
    L, L1 = "  " * level, "  " * (level + 1)
    items = []
    if p.access != 0:
        items += _item("Access", "gh_int32", "3", p.access, level + 2)
    items += _item("AllowTreeAccess", "gh_bool", "1", _bool(is_input), level + 2)
    items += _item("Description", "gh_string", "10", tooltip, level + 2)
    items += _item("InstanceGuid", "gh_guid", "9", guid, level + 2)
    items += _item("Name", "gh_string", "10", p.nickname, level + 2)
    items += _item("NickName", "gh_string", "10", p.nickname, level + 2)
    items += _item("Optional", "gh_bool", "1", _bool(p.optional), level + 2)
    items += _item("ScriptParamAccess", "gh_int32", "3", p.access, level + 2)
    items += _item("ScriptParameterVersion", "gh_int32", "3", 2, level + 2)
    items += _item("ShowTypeHints", "gh_bool", "1", "true", level + 2)
    items += _item("SourceCount", "gh_int32", "3", 0, level + 2)
    items += _item("ToolTip", "gh_string", "10", tooltip, level + 2)
    items += _item("TypeHintID", "gh_guid", "9", p.hint.type_hint_id, level + 2)
    count = 13 if p.access != 0 else 12
    out = ["%s<chunk name=\"%s\" index=\"%d\">" % (L, tag, index),
           "%s<items count=\"%d\">" % (L1, count)]
    out += items
    out += ["%s</items>" % L1, "%s<chunks count=\"2\">" % L1]
    out += _attr_chunk(x, y, 31, 136, level + 2)
    out += _converter_chunk(p.hint, level + 2)
    out += ["%s</chunks>" % L1, "%s</chunk>" % L]
    return out


def _std_out_chunk(index, guid, x, y, level):
    """The always-first 6-item standard 'out' stdout OutputParam (no hint)."""
    L, L1 = "  " * level, "  " * (level + 1)
    out = ["%s<chunk name=\"OutputParam\" index=\"%d\">" % (L, index),
           "%s<items count=\"6\">" % L1]
    out += _item("Description", "gh_string", "10", _STANDARD_OUT_DESC, level + 2)
    out += _item("InstanceGuid", "gh_guid", "9", guid, level + 2)
    out += _item("Name", "gh_string", "10", "out", level + 2)
    out += _item("NickName", "gh_string", "10", "out", level + 2)
    out += _item("Optional", "gh_bool", "1", "false", level + 2)
    out += _item("SourceCount", "gh_int32", "3", 0, level + 2)
    out += ["%s</items>" % L1, "%s<chunks count=\"1\">" % L1]
    out += _attr_chunk(x, y, 25, 136, level + 2)
    out += ["%s</chunks>" % L1, "%s</chunk>" % L]
    return out


def _parameter_data(inputs, user_outputs, relpath, fresh, level):
    """The ParameterData chunk: InputId/OutputId tables + per-param chunks.

    Output 0 is always the standard 'out' stdout param; user outputs follow.
    """
    L, L1 = "  " * level, "  " * (level + 1)
    n_in, n_out = len(inputs), 1 + len(user_outputs)
    items = ["%s<item name=\"InputCount\" type_name=\"gh_int32\" type_code=\"3\">%d</item>" % (L1, n_in)]
    for i in range(n_in):
        items.append("%s<item name=\"InputId\" index=\"%d\" type_name=\"gh_guid\" type_code=\"9\">%s</item>"
                     % (L1, i, SCRIPT_VAR_PARAM))
    items.append("%s<item name=\"OutputCount\" type_name=\"gh_int32\" type_code=\"3\">%d</item>" % (L1, n_out))
    out_ids = [STANDARD_OUT_PARAM] + [SCRIPT_VAR_PARAM] * len(user_outputs)
    for i, oid in enumerate(out_ids):
        items.append("%s<item name=\"OutputId\" index=\"%d\" type_name=\"gh_guid\" type_code=\"9\">%s</item>"
                     % (L1, i, oid))
    o = ["%s<chunk name=\"ParameterData\">" % L,
         "%s<items count=\"%d\">" % (L1, 1 + n_in + 1 + n_out)]
    o += items
    o += ["%s</items>" % L1, "%s<chunks count=\"%d\">" % (L1, n_in + n_out)]
    y = 105
    for i, p in enumerate(inputs):
        guid = _instance_guid(relpath, "in", p.nickname, fresh)
        o += _user_param_chunk("InputParam", i, p, guid, _tooltip(p.pytype, p.description), 273, y, level + 2)
        y += 136
    o += _std_out_chunk(0, _instance_guid(relpath, "out", "__stdout__", fresh), 328, 105, level + 2)
    y = 241
    for i, p in enumerate(user_outputs):
        guid = _instance_guid(relpath, "out", p.nickname, fresh)
        o += _user_param_chunk("OutputParam", i + 1, p, guid, _tooltip(p.pytype, p.description), 328, y, level + 2)
        y += 136
    o += ["%s</chunks>" % L1, "%s</chunk>" % L]
    return "\n".join(o)


def _script_chunk(code_text, title, level):
    """The Script chunk: base64(code, CRLF) + the python-3 LanguageSpec."""
    L, L1, L2 = "  " * level, "  " * (level + 1), "  " * (level + 2)
    crlf = code_text.replace("\r\n", "\n").replace("\n", "\r\n")
    b64 = base64.b64encode(crlf.encode("utf-8")).decode("ascii")
    o = ["%s<chunk name=\"Script\">" % L, "%s<items count=\"5\">" % L1]
    o += _item("MarshGuids", "gh_bool", "1", "true", level + 2)
    o += _item("MarshInputs", "gh_bool", "1", "true", level + 2)
    o += _item("MarshOutputs", "gh_bool", "1", "true", level + 2)
    o += _item("Text", "gh_string", "10", b64, level + 2)
    o += _item("Title", "gh_string", "10", title, level + 2)
    o += ["%s</items>" % L1, "%s<chunks count=\"1\">" % L1,
          "%s<chunk name=\"LanguageSpec\">" % L1, "%s<items count=\"2\">" % L2]
    o += _item("Taxon", "gh_string", "10", "*.*.python", level + 3)
    o += _item("Version", "gh_string", "10", "3.*", level + 3)
    o += ["%s</items>" % L2, "%s</chunk>" % L1, "%s</chunks>" % L1, "%s</chunk>" % L]
    return "\n".join(o)


# Fixed clipboard-archive scaffolding. {placeholders} are filled by build_archive;
# {parameter_data} / {script} are pre-rendered chunk blocks.
_ARCHIVE_TEMPLATE = """<Archive name="Root">
  <items count="1">
    <item name="ArchiveVersion" type_name="gh_version" type_code="80">
      <Major>0</Major>
      <Minor>2</Minor>
      <Revision>2</Revision>
    </item>
  </items>
  <chunks count="1">
    <chunk name="Clipboard">
      <items count="1">
        <item name="plugin_version" type_name="gh_version" type_code="80">
          <Major>1</Major>
          <Minor>0</Minor>
          <Revision>8</Revision>
        </item>
      </items>
      <chunks count="7">
        <chunk name="DocumentHeader">
          <items count="5">
            <item name="DocumentID" type_name="gh_guid" type_code="9">{doc_id}</item>
            <item name="Preview" type_name="gh_string" type_code="10">Shaded</item>
            <item name="PreviewMeshType" type_name="gh_int32" type_code="3">1</item>
            <item name="PreviewNormal" type_name="gh_drawing_color" type_code="36">
              <ARGB>100;150;0;0</ARGB>
            </item>
            <item name="PreviewSelected" type_name="gh_drawing_color" type_code="36">
              <ARGB>100;0;150;0</ARGB>
            </item>
          </items>
        </chunk>
        <chunk name="DefinitionProperties">
          <items count="4">
            <item name="Date" type_name="gh_date" type_code="8">{date}</item>
            <item name="Description" type_name="gh_string" type_code="10"></item>
            <item name="KeepOpen" type_name="gh_bool" type_code="1">false</item>
            <item name="Name" type_name="gh_string" type_code="10"></item>
          </items>
          <chunks count="3">
            <chunk name="Revisions">
              <items count="1">
                <item name="RevisionCount" type_name="gh_int32" type_code="3">0</item>
              </items>
            </chunk>
            <chunk name="Projection">
              <items count="2">
                <item name="Target" type_name="gh_drawing_point" type_code="30">
                  <X>0</X>
                  <Y>0</Y>
                </item>
                <item name="Zoom" type_name="gh_single" type_code="5">1</item>
              </items>
            </chunk>
            <chunk name="Views">
              <items count="1">
                <item name="ViewCount" type_name="gh_int32" type_code="3">0</item>
              </items>
            </chunk>
          </chunks>
        </chunk>
        <chunk name="RcpLayout">
          <items count="1">
            <item name="GroupCount" type_name="gh_int32" type_code="3">0</item>
          </items>
        </chunk>
        <chunk name="ValueTable">
          <items count="0"></items>
        </chunk>
        <chunk name="Author">
          <items count="1">
            <item name="Name" type_name="gh_string" type_code="10">{author}</item>
          </items>
        </chunk>
        <chunk name="GHALibraries">
          <items count="1">
            <item name="Count" type_name="gh_int32" type_code="3">1</item>
          </items>
          <chunks count="1">
            <chunk name="Library" index="0">
              <items count="4">
                <item name="Author" type_name="gh_string" type_code="10">{lib_author}</item>
                <item name="Id" type_name="gh_guid" type_code="9">{lib_id}</item>
                <item name="Name" type_name="gh_string" type_code="10">{lib_name}</item>
                <item name="Version" type_name="gh_string" type_code="10">{lib_version}</item>
              </items>
            </chunk>
          </chunks>
        </chunk>
        <chunk name="DefinitionObjects">
          <items count="1">
            <item name="ObjectCount" type_name="gh_int32" type_code="3">1</item>
          </items>
          <chunks count="1">
            <chunk name="Object" index="0">
              <items count="2">
                <item name="GUID" type_name="gh_guid" type_code="9">{comp_type}</item>
                <item name="Name" type_name="gh_string" type_code="10">Python 3 Script</item>
              </items>
              <chunks count="1">
                <chunk name="Container">
                  <items count="14">
                    <item name="Description" type_name="gh_string" type_code="10">{comp_desc}</item>
                    <item name="GraftStandardOutputLines" type_name="gh_bool" type_code="1">true</item>
                    <item name="InstanceGuid" type_name="gh_guid" type_code="9">{comp_instguid}</item>
                    <item name="MarshGuids" type_name="gh_bool" type_code="1">true</item>
                    <item name="MarshInputs" type_name="gh_bool" type_code="1">true</item>
                    <item name="MarshOutputs" type_name="gh_bool" type_code="1">true</item>
                    <item name="Name" type_name="gh_string" type_code="10">Python 3 Script</item>
                    <item name="NickName" type_name="gh_string" type_code="10">{nickname}</item>
                    <item name="ScriptComponentVersion" type_name="gh_int32" type_code="3">3</item>
                    <item name="Tooltip" type_name="gh_string" type_code="10">{comp_desc}</item>
                    <item name="UsingLibraryInputParam" type_name="gh_bool" type_code="1">false</item>
                    <item name="UsingScriptInputParam" type_name="gh_bool" type_code="1">false</item>
                    <item name="UsingScriptOutputParam" type_name="gh_bool" type_code="1">false</item>
                    <item name="UsingStandardOutputParam" type_name="gh_bool" type_code="1">true</item>
                  </items>
                  <chunks count="4">
                    <chunk name="Attributes">
                      <items count="3">
                        <item name="Bounds" type_name="gh_drawing_rectanglef" type_code="35">
                          <X>100</X>
                          <Y>100</Y>
                          <W>84</W>
                          <H>{comp_h}</H>
                        </item>
                        <item name="Pivot" type_name="gh_drawing_pointf" type_code="31">
                          <X>142</X>
                          <Y>{comp_pivot_y}</Y>
                        </item>
                        <item name="Selected" type_name="gh_bool" type_code="1">true</item>
                      </items>
                    </chunk>
{parameter_data}
{script}
                    <chunk name="ScriptEditor">
                      <items count="1">
                        <item name="StartBounds" type_name="gh_drawing_rectangle" type_code="34">
                          <X>200</X>
                          <Y>200</Y>
                          <W>550</W>
                          <H>600</H>
                        </item>
                      </items>
                    </chunk>
                  </chunks>
                </chunk>
              </chunks>
            </chunk>
          </chunks>
        </chunk>
      </chunks>
    </chunk>
  </chunks>
</Archive>
"""


def build_archive(inputs, user_outputs, code_text, component_desc, nickname,
                  author=_AUTHOR_DEFAULT, relpath="", fresh_guids=False) -> str:
    """Assemble a full GH clipboard archive for one Python 3 Script component."""
    esc = _xml_escape
    rows = max(len(inputs), 1 + len(user_outputs), 1)
    comp_h = 24 + rows * 48
    return _ARCHIVE_TEMPLATE.format(
        doc_id=_instance_guid(relpath, "doc", nickname, fresh_guids),
        date=_DATE_TICKS,
        author=esc(author),
        lib_author=esc(_GH_LIB["Author"]), lib_id=_GH_LIB["Id"],
        lib_name=esc(_GH_LIB["Name"]), lib_version=esc(_GH_LIB["Version"]),
        comp_type=COMPONENT_GUID,
        comp_desc=esc(component_desc), nickname=esc(nickname),
        comp_instguid=_instance_guid(relpath, "component", nickname, fresh_guids),
        comp_h=comp_h, comp_pivot_y=100 + comp_h / 2.0,
        parameter_data=_parameter_data(inputs, user_outputs, relpath, fresh_guids, 10),
        script=_script_chunk(code_text, nickname, 10),
    )


# ---------------------------------------------------------------------------
# File / repo helpers
# ---------------------------------------------------------------------------
def repo_relpath(path: str) -> str:
    """Repo-relative POSIX path (for stable GUIDs); basename if no repo root."""
    p = os.path.abspath(path)
    d = os.path.dirname(p)
    while True:
        if os.path.isdir(os.path.join(d, ".git")):
            return os.path.relpath(p, d).replace(os.sep, "/")
        parent = os.path.dirname(d)
        if parent == d:
            return os.path.basename(p)
        d = parent


# ---------------------------------------------------------------------------
# lib inlining (--inline-lib capability): the five lib-importing components
# use a module-level try/except shim whose inspect.getfile fallback is dead
# code in a pasted component. At archive-gen time the shim is replaced by the
# needed lib definitions so every sidecar is self-contained.
# ---------------------------------------------------------------------------

def _find_lib_shim(tree, lib_names):
    """Module-level Try whose body is only `from <lib module> import ...`.

    Returns (try_node, {module: [imported names]}) or (None, {}).
    """
    for node in tree.body:
        if not isinstance(node, ast.Try):
            continue
        wanted = {}
        for stmt in node.body:
            if (isinstance(stmt, ast.ImportFrom) and stmt.level == 0
                    and stmt.module in lib_names):
                wanted.setdefault(stmt.module, []).extend(
                    a.name for a in stmt.names)
            else:
                wanted = {}
                break
        if wanted:
            return node, wanted
    return None, {}


def _import_bound_names(node):
    """Names an Import/ImportFrom statement binds in the module namespace."""
    out = []
    for a in node.names:
        out.append(a.asname if a.asname else a.name.split(".")[0])
    return out


def inline_lib_imports(src, lib_dir):
    """Replace the lib-import shim with the needed lib definitions.

    Returns `src` unchanged when there is no shim or no lib_dir. The spliced
    block carries the lib module's own import statements that the inlined
    code references; `#!` / `# r:` lines are comments and never carried
    (extraction is ast-segment based).
    """
    if not lib_dir or not os.path.isdir(lib_dir):
        return src
    lib_names = {os.path.splitext(f)[0]
                 for f in os.listdir(lib_dir) if f.endswith(".py")}
    tree = ast.parse(src)
    shim, wanted = _find_lib_shim(tree, lib_names)
    if shim is None:
        return src

    blocks = []
    for module in sorted(wanted):
        with open(os.path.join(lib_dir, module + ".py"), "r",
                  encoding="utf-8") as f:
            mod_src = f.read()
        mod_lines = mod_src.splitlines()
        mod_tree = ast.parse(mod_src)

        defs = {}       # top-level name -> defining node
        order = []      # defining nodes in source order (stable output)
        imports = []    # top-level Import/ImportFrom nodes
        for n in mod_tree.body:
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef,
                              ast.ClassDef)):
                defs[n.name] = n
                order.append(n)
            elif isinstance(n, ast.Assign):
                for t in n.targets:
                    if isinstance(t, ast.Name):
                        defs[t.id] = n
                order.append(n)
            elif isinstance(n, (ast.Import, ast.ImportFrom)):
                imports.append(n)

        missing = sorted(set(wanted[module]) - set(defs))
        if missing:
            raise ParamConventionError(
                "--inline-lib: %s does not define %s"
                % (module, ", ".join(missing)))

        # Transitive closure: a needed def may call other top-level defs the
        # component never imports (e.g. compute_face_normals -> normalize_vectors).
        needed = set()
        stack = list(wanted[module])
        while stack:
            name = stack.pop()
            if name in needed:
                continue
            needed.add(name)
            stack.extend(ref for ref in
                         {x.id for x in ast.walk(defs[name])
                          if isinstance(x, ast.Name)}
                         if ref in defs and ref not in needed)
        picked = [n for n in order
                  if (getattr(n, "name", None) in needed
                      or any(isinstance(t, ast.Name) and t.id in needed
                             for t in getattr(n, "targets", [])))]

        # Import carriage: only the lib imports the inlined code references.
        referenced = set()
        for n in picked:
            referenced |= {x.id for x in ast.walk(n)
                           if isinstance(x, ast.Name)}
        carried = [n for n in imports
                   if set(_import_bound_names(n)) & referenced]

        seg = ["# --- inlined from lib/%s.py by gh_params_gen "
               "(self-contained sidecar) ---" % module]
        for n in carried + picked:
            seg.append("\n".join(mod_lines[n.lineno - 1:n.end_lineno]))
        blocks.append("\n\n".join(seg))
    blocks.append("# --- end inlined lib code ---")

    src_lines = src.splitlines()
    new_lines = (src_lines[:shim.lineno - 1]
                 + "\n\n".join(blocks).splitlines()
                 + src_lines[shim.end_lineno:])
    out = "\n".join(new_lines)
    return out + ("\n" if src.endswith("\n") else "")


def _warn_domain_mismatch(script_path, src, warnings):
    """Docstring header `<name> — <domain>` should match the ghpython folder."""
    folder = os.path.basename(os.path.dirname(os.path.abspath(script_path)))
    parent = os.path.basename(
        os.path.dirname(os.path.dirname(os.path.abspath(script_path))))
    if parent != "ghpython":
        return
    doc = _module_docstring(src)
    first = next((ln.strip() for ln in doc.splitlines() if ln.strip()), "")
    m = re.match(r"\S+\s+—\s+(\w+)", first)
    if m and m.group(1) != folder:
        warnings.append(
            "docstring header says '%s' but the file lives in ghpython/%s/"
            % (m.group(1), folder))


def default_sidecar(script_path: str) -> str:
    return os.path.splitext(os.path.abspath(script_path))[0] + ".ghcomp.xml"


_PY2_SHEBANG = re.compile(r"^#!\s*python\s*2\b")


def generate(script_path: str, fresh_guids=False):
    """Parse a script and return (xml | None, ParseResult). None xml = no-op.

    The whole `.py` is embedded as the component's runnable code, so pasting the
    archive yields a working Python 3 Script component.
    """
    with open(script_path, "r", encoding="utf-8") as f:
        src = f.read()
    first = src.splitlines()[0] if src else ""
    if _PY2_SHEBANG.match(first.strip()):
        raise ParamConventionError(
            "this is a '#! python 2' (IronPython) script; only the Python 3 Script "
            "component is supported. Convert to '#! python 3' or generate it by hand.")
    result = parse_docstring(src)
    if not result.has_sections:
        return None, result
    _warn_domain_mismatch(script_path, src, result.warnings)
    # Self-contained sidecars: splice lib imports before embedding. Same
    # repo-layout convention as the components' own shim (../../lib).
    lib_dir = os.path.normpath(os.path.join(
        os.path.dirname(os.path.abspath(script_path)), "..", "..", "lib"))
    src = inline_lib_imports(src, lib_dir)
    # Repo→canvas identity (deterministic, changes iff the embedded code
    # changes): truncated sha256 of the final spliced LF source, stamped
    # into the component description. Map hash → human version at release
    # time in the CHANGELOG.
    src_hash = hashlib.sha256(src.encode("utf-8")).hexdigest()[:8]
    desc = "%s\n[src %s]" % (result.component_desc, src_hash)
    nickname = os.path.splitext(os.path.basename(script_path))[0]
    xml = build_archive(result.inputs, result.outputs, code_text=src,
                        component_desc=desc, nickname=nickname,
                        relpath=repo_relpath(script_path), fresh_guids=fresh_guids)
    return xml, result


def _copy_to_clipboard(text: str) -> bool:
    try:
        subprocess.run(["powershell", "-NoProfile", "-Command", "$input | Set-Clipboard"],
                       input=text, text=True, check=True)
        return True
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Batch mode + catalog
# ---------------------------------------------------------------------------
def _component_scripts(root):
    import glob as _glob
    return sorted(_glob.glob(os.path.join(root, "ghpython", "*", "*.py")))


def _catalog_row(script, xml, result, root):
    with open(script, "r", encoding="utf-8") as f:
        head = f.read(2048)
    venv = re.search(r"^# venv:\s*(\S+)", head, re.M)
    src_hash = re.search(r"\[src ([0-9a-f]{8})\]", xml)
    # The splice marker lives inside the base64 Text item, not the raw XML.
    code_b64 = re.search(r'name="Text"[^>]*>([^<]+)</item>', xml)
    code = (base64.b64decode(code_b64.group(1)).decode("utf-8")
            if code_b64 else "")
    purpose = result.component_desc.split(". ")[0].rstrip(".") + "."
    rel = os.path.relpath(script, root).replace(os.sep, "/")
    return "| %s | %s | %s | %d in / %d out | %s | %s | `%s` |" % (
        os.path.splitext(os.path.basename(script))[0],
        rel.split("/")[1],
        purpose,
        len(result.inputs), len(result.outputs),
        venv.group(1) if venv else "—",
        "yes (lib inlined)" if "inlined from lib/" in code else "yes",
        src_hash.group(1) if src_hash else "?")


_CATALOG_PREAMBLE = """\
# Component catalog

Generated — do not edit by hand; refresh with
`python tools/gh_params_gen.py --catalog` (env: gh-tools).

To use a component: open its `<name>.ghcomp.xml` sidecar, select all, copy,
and press Ctrl-V on a Grasshopper canvas (Rhino 8). The whole component
appears — embedded code, params, tooltips, description. The `src` column is
the content hash also stamped into the component's description on canvas.

| Component | Domain | Purpose | I/O | venv | Self-contained | src |
|---|---|---|---|---|---|---|
"""


def _run_batch(args, root) -> int:
    rc = 0
    rows = []
    for script in _component_scripts(root):
        try:
            xml, result = generate(script, fresh_guids=args.fresh)
        except ParamConventionError as ex:
            print("gh_params_gen: %s: %s" % (script, ex), file=sys.stderr)
            rc = max(rc, 2)
            continue
        if xml is None:
            continue
        for w in result.warnings:
            print("gh_params_gen: warning: %s: %s" % (script, w), file=sys.stderr)
        if args.all:
            out_path = default_sidecar(script)
            if args.check:
                current = None
                if os.path.isfile(out_path):
                    with open(out_path, "r", encoding="utf-8") as f:
                        current = f.read()
                if current != xml:
                    print("gh_params_gen: stale or missing sidecar: %s" % out_path,
                          file=sys.stderr)
                    rc = max(rc, 1)
            else:
                with open(out_path, "w", encoding="utf-8", newline="\n") as f:
                    f.write(xml)
                if not args.quiet:
                    print("gh_params_gen: %s -> %s" % (script, out_path))
        if args.catalog:
            rows.append(_catalog_row(script, xml, result, root))
    if args.catalog:
        path = (os.path.join(root, "docs", "components.md")
                if args.catalog == "__default__" else args.catalog)
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(_CATALOG_PREAMBLE + "\n".join(rows) + "\n")
        if not args.quiet:
            print("gh_params_gen: catalog -> %s  (%d components)" % (path, len(rows)))
    return rc


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="Generate a whole Python 3 Script component archive from a script docstring.")
    ap.add_argument("script", nargs="?",
                    help="path to the GhPython component script (omit with --all/--catalog)")
    ap.add_argument("--out", help="output path (default: <script>.ghcomp.xml)")
    ap.add_argument("--stdout", action="store_true", help="print XML to stdout, write nothing")
    ap.add_argument("--clipboard", action="store_true",
                    help="copy the archive to the Windows clipboard (paste onto the GH canvas)")
    ap.add_argument("--fresh-guids", dest="fresh", action="store_true",
                    help="use random uuid4 InstanceGuids instead of deterministic uuid5")
    ap.add_argument("--check", action="store_true",
                    help="exit non-zero if the on-disk sidecar differs; write nothing")
    ap.add_argument("--all", action="store_true",
                    help="process every ghpython/<domain>/*.py sidecar (write, or verify with --check)")
    ap.add_argument("--catalog", nargs="?", const="__default__", metavar="PATH",
                    help="write the component catalog markdown (default: docs/components.md)")
    ap.add_argument("--root", help=argparse.SUPPRESS)  # repo root override (tests)
    ap.add_argument("--quiet", action="store_true", help="suppress the summary line")
    args = ap.parse_args(argv)

    if args.all or args.catalog:
        if args.script:
            ap.error("--all/--catalog take no script argument")
        root = os.path.abspath(args.root) if args.root else (
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        return _run_batch(args, root)
    if not args.script:
        ap.error("script is required unless --all/--catalog is given")

    if not os.path.isfile(args.script):
        print("gh_params_gen: not a file: %s" % args.script, file=sys.stderr)
        return 1

    try:
        xml, result = generate(args.script, fresh_guids=args.fresh)
    except ParamConventionError as ex:
        print("gh_params_gen: %s: %s" % (args.script, ex), file=sys.stderr)
        return 2

    if xml is None:
        if not args.quiet:
            print("gh_params_gen: %s: no Grasshopper Inputs/Outputs sections; skipped." % args.script)
        return 0

    for w in result.warnings:
        print("gh_params_gen: warning: %s" % w, file=sys.stderr)

    out_path = args.out or default_sidecar(args.script)

    if args.check:
        current = None
        if os.path.isfile(out_path):
            with open(out_path, "r", encoding="utf-8") as f:
                current = f.read()
        if current != xml:
            print("gh_params_gen: stale or missing sidecar: %s" % out_path, file=sys.stderr)
            return 1
        return 0

    if args.stdout:
        sys.stdout.write(xml)
    else:
        with open(out_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(xml)

    if args.clipboard and not _copy_to_clipboard(xml):
        print("gh_params_gen: warning: could not copy to clipboard (Set-Clipboard unavailable)",
              file=sys.stderr)

    if not args.quiet:
        where = "stdout" if args.stdout else out_path
        print("gh_params_gen: %s -> %s  (%d inputs, %d outputs)"
              % (args.script, where, len(result.inputs), len(result.outputs)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
