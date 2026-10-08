#!/usr/bin/env python3
"""Index the PS2 decompilation (crowded-street/3s-decomp) into per-function features.
usage: ps2_index.py <3s-decomp dir> <out.json> [overlay dir]
Functions defined in the overlay dir (arcade-specific C) replace the PS2 ones of the same name.
Output: {"functions": [name, file, addr, size, order, consts, calls, lines], "tables": [name, file, owner, items]}
`size` is the distance to the next PS2 function symbol. `tables` are initialisers holding function pointers
(items are function names, or null for anything else)."""
import bisect, json, os, re, sys
import tree_sitter_c
from tree_sitter import Language, Parser

ref, out = sys.argv[1], sys.argv[2]
syms = {}; all_addrs = []
for line in open(os.path.join(ref, "config/anniversary/symbols/syms_sfiii.txt")):
    m = re.match(r"\s*(\w+)\s*=\s*(0x[0-9A-Fa-f]+);\s*//(.*)", line)
    if not m or "type:func" not in m.group(3): continue
    syms[m.group(1)] = int(m.group(2), 16); all_addrs.append(int(m.group(2), 16))
all_addrs.sort()
def size_of(a):
    i = bisect.bisect_right(all_addrs, a)
    return all_addrs[i] - a if a and i < len(all_addrs) else 0

parser = Parser(Language(tree_sitter_c.language()))

def num(text):
    t = text.decode().rstrip("uUlLfF") if not text.lower().startswith(b"0x") else text.decode().rstrip("uUlL")
    try: return int(t, 0)
    except ValueError:
        try: return int(t.lstrip("0") or "0")
        except ValueError: return None

def idents(body, params):
    """Identifiers used in a body that are not locals or parameters (globals, macros, enum constants), in order."""
    local = set(params); seen = []; st = [body]
    decl_ids = set()
    def declared(n):
        while n is not None and n.type != "identifier":
            n = n.child_by_field_name("declarator")
        return n
    nodes = []
    while st:
        n = st.pop(); nodes.append(n); st.extend(reversed(n.children))
    for n in nodes:
        if n.type == "declaration":
            for ch in n.named_children:
                d = declared(ch if ch.type != "init_declarator" else ch.child_by_field_name("declarator")) if ch.type in ("init_declarator", "identifier", "pointer_declarator", "array_declarator") else None
                if d is not None: local.add(d.text.decode()); decl_ids.add(d.id)
    for n in nodes:
        if n.type == "identifier" and n.id not in decl_ids:
            t = n.text.decode()
            if t not in local and t not in seen: seen.append(t)
    return seen

def walk(node, consts, calls, neg=False):
    if node.type == "number_literal":
        v = num(node.text)
        if v is not None: consts.append(-v if neg else v)
        return
    if node.type == "call_expression":
        fn = node.child_by_field_name("function")
        if fn is not None and fn.type == "identifier": calls.append(fn.text.decode())
    for ch in node.children:
        walk(ch, consts, calls, node.type == "unary_expression" and node.children[0].type == "-")

def fname(decl):
    while decl is not None and decl.type != "identifier":
        decl = decl.child_by_field_name("declarator")
    return decl.text.decode() if decl is not None else None

recs = []; raw_tables = []

def flat(node, out):
    for ch in node.named_children:
        if ch.type == "initializer_list": flat(ch, out)
        elif ch.type == "comment": continue
        elif ch.type == "initializer_pair": flat(ch, out)
        elif ch.type == "identifier": out.append(ch.text.decode())
        elif ch.type == "pointer_expression" and ch.named_child_count == 1 and ch.named_children[0].type == "identifier":
            out.append(ch.named_children[0].text.decode())
        elif ch.type in ("field_designator", "subscript_designator"): continue
        else: out.append(None)

def tables_in(node):
    res = []; st = [node]
    while st:
        n = st.pop()
        if n.type == "init_declarator":
            val = n.child_by_field_name("value")
            if val is not None and val.type == "initializer_list":
                items = []; flat(val, items)
                res.append((fname(n.child_by_field_name("declarator")), items)); continue
        st.extend(reversed(n.children))
    return res
src = os.path.join(ref, "src/anniversary/sf33rd")
overlay = sys.argv[3] if len(sys.argv) > 3 else None
walks = list(sorted(os.walk(src))) + (list(sorted(os.walk(overlay))) if overlay else [])
for root, _, files in walks:
    for fn in sorted(files):
        if not fn.endswith(".c"): continue
        path = os.path.join(root, fn)
        tree = parser.parse(open(path, "rb").read())
        stack = [tree.root_node]
        while stack:
            n = stack.pop()
            if n.type == "function_definition":
                name = fname(n.child_by_field_name("declarator"))
                body = n.child_by_field_name("body")
                if name and body is not None:
                    consts, calls = [], []
                    walk(body, consts, calls)
                    a = syms.get(name, 0)
                    pl = n.child_by_field_name("declarator").child_by_field_name("parameters")
                    params = [fname(p) or "" for p in pl.named_children if p.type == "parameter_declaration"] if pl is not None else []
                    for t in tables_in(body): raw_tables.append((os.path.relpath(path, src), name, *t))
                    recs.append(dict(name=name, file=os.path.relpath(path, src), addr=a, size=size_of(a),
                                     consts=consts, calls=calls, idents=idents(body, params), lines=body.end_point[0] - body.start_point[0]))
            elif n.type == "declaration":
                for t in tables_in(n): raw_tables.append((os.path.relpath(path, src), None, *t))
            else:
                stack.extend(reversed(n.children))
if overlay:                              # later definitions (overlay) win; they keep the PS2 file for ordering
    first = {}; over = 0
    for r in recs:
        if r["name"] in first and r["file"].startswith(".."):
            r["file"] = first[r["name"]]["file"]; r["overlay"] = True; first[r["name"]]["dead"] = True; over += 1
        else: first[r["name"]] = r
    recs = [r for r in recs if not r.get("dead")]
    print(f"{over} functions overridden by arcade-specific source")
recs.sort(key=lambda r: (r["addr"] == 0, r["addr"]))
for i, r in enumerate(recs): r["order"] = i
names = {r["name"] for r in recs} | set(syms)
tables = []
for f, owner, tname, items in raw_tables:
    items = [x if x in names else None for x in items]
    if sum(x is not None for x in items) >= 2:
        tables.append(dict(name=tname, file=f, owner=owner, items=items))
json.dump(dict(functions=recs, tables=tables), open(out, "w"))
print(f"{len(tables)} function-pointer tables, {sum(len(t['items']) for t in tables)} entries")
print(f"{len(recs)} functions from source; {sum(1 for r in recs if r['addr'])} with PS2 address; "
      f"{len({r['file'] for r in recs})} files")
