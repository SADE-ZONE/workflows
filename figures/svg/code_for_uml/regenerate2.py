#!/usr/bin/env python3
import argparse
from pathlib import Path
import re
from xml.etree import ElementTree as ET


def local(tag: str) -> str:
    return tag.split("}", 1)[-1] if "}" in tag else tag


def has_class(elem, needle: str) -> bool:
    cls = elem.get("class", "")
    return needle in cls.split() or needle in cls


def parse_viewbox(vb: str):
    parts = vb.strip().split()
    if len(parts) != 4:
        return None
    return [float(p) for p in parts]


def fmt_viewbox(v):
    # keep integers pretty
    out = []
    for x in v:
        out.append(str(int(x)) if float(x).is_integer() else str(x))
    return " ".join(out)


Y_ATTRS = ("y", "y1", "y2", "cy")  # extend if needed


def main():
    ap = argparse.ArgumentParser(
        description="Resize Mermaid sequence actor boxes + shift diagram; writes to parsed/<name>.svg"
    )
    ap.add_argument("in_svg", help="Input SVG file (e.g., test1.svg)")
    ap.add_argument("--height", type=float, default=30.0, help="New actor box height (default 30)")
    args = ap.parse_args()

    in_path = Path(args.in_svg)
    if not in_path.exists():
        raise SystemExit(f"Input not found: {in_path}")

    out_dir = in_path.parent / "parsed"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / in_path.name

    tree = ET.parse(in_path)
    root = tree.getroot()

    # Namespace
    m = re.match(r"^\{([^}]+)\}", root.tag)
    ns_uri = m.group(1) if m else ""
    ns = {"svg": ns_uri} if ns_uri else {}

    def findall(path):
        return root.findall(path, ns) if ns else root.findall(path.replace("svg:", ""))

    # ---- 1) Find old actor height from an actor-top rect ----
    actor_top_rects = []
    for r in findall(".//svg:rect"):
        if local(r.tag) == "rect" and has_class(r, "actor-top"):
            actor_top_rects.append(r)

    if not actor_top_rects:
        raise SystemExit("Couldn't find any actor-top rectangles. Is this a Mermaid sequence SVG?")

    old_h = float(actor_top_rects[0].get("height", "65"))
    new_h = float(args.height)
    delta = new_h - old_h

    if abs(delta) < 1e-6:
        tree.write(out_path, encoding="utf-8", xml_declaration=False)
        print(f"No change needed; wrote: {out_path}")
        return

    # ---- 2) Resize actor top/bottom rects and re-center their text ----
    # Mermaid structure: <g><rect class="actor actor-top"> <text class="actor actor-box">...</text></g>
    for g in findall(".//svg:g"):
        children = list(g)

        rects = [c for c in children if local(c.tag) == "rect" and has_class(c, "actor")]
        texts = [c for c in children if local(c.tag) == "text" and has_class(c, "actor-box")]

        if rects:
            rect = rects[0]
            if has_class(rect, "actor-top") or has_class(rect, "actor-bottom"):
                # resize
                rect.set("height", str(new_h))
                # recenter matching text if present
                if texts:
                    t = texts[0]
                    ry = float(rect.get("y", "0"))
                    t.set("y", str(ry + new_h / 2.0))

    # ---- 3) Fix lifeline start y1 from old_h -> new_h ----
    for ln in findall(".//svg:line"):
        if local(ln.tag) == "line" and has_class(ln, "actor-line"):
            # Only adjust lifeline start; end will be shifted in step 4
            y1 = float(ln.get("y1", "0"))
            if abs(y1 - old_h) < 0.5:  # close enough
                ln.set("y1", str(new_h))

    # ---- 4) Shift everything below the old top-box height down by delta ----
    # We do this generically for elements with y/y1/y2/cy attributes.
    for elem in root.iter():
        # Skip the actor-top rect/text y=0 group adjustments already handled:
        # (those start at y=0 or y=old_h/2; shifting them would be wrong)
        # So only shift coordinates >= old_h (i.e., content below top actor boxes).
        for attr in Y_ATTRS:
            if attr in elem.attrib:
                try:
                    v = float(elem.attrib[attr])
                except ValueError:
                    continue
                if v >= old_h - 0.01:  # below the original top box bottom
                    elem.set(attr, str(v + delta))

    # ---- 5) Expand viewBox height so nothing clips ----
    vb = root.get("viewBox")
    if vb:
        vbv = parse_viewbox(vb)
        if vbv:
            vbv[3] = vbv[3] + delta  # increase height
            root.set("viewBox", fmt_viewbox(vbv))

    tree.write(out_path, encoding="utf-8", xml_declaration=False)
    print(f"Wrote: {out_path}")


if __name__ == "__main__":
    main()
