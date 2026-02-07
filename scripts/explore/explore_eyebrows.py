# Explore Luna Eyebrow Components
# ================================
# Find eyebrow geometry in Luna model for tracking setup
#
# exec(open(project.folder + '/explore_eyebrows.py').read())

print("\n" + "=" * 70)
print("EXPLORING LUNA MODEL FOR EYEBROW COMPONENTS")
print("=" * 70)

LUNA_PATH = '/project1/luna_container/Luna'

luna = op(LUNA_PATH)
if luna is None:
    print(f"ERROR: Luna not found at {LUNA_PATH}")
else:
    print(f"\nLuna FBX: {luna.path}")
    print(f"Children ({len(luna.children)}):\n")

    # Look for eyebrow-related components
    eyebrow_candidates = []
    all_comps = []

    for child in luna.children:
        name_lower = child.name.lower()
        child_type = type(child).__name__

        all_comps.append((child.name, child_type))

        # Check for eyebrow-related names
        if any(kw in name_lower for kw in ['brow', 'eyebrow', 'eye']):
            eyebrow_candidates.append(child)

    # Print all components
    print("All components:")
    for name, ctype in sorted(all_comps):
        marker = " <-- EYEBROW?" if any(kw in name.lower() for kw in ['brow', 'eyebrow']) else ""
        marker = " <-- EYE?" if 'eye' in name.lower() and not marker else marker
        print(f"  {name} ({ctype}){marker}")

    # Detail on eyebrow candidates
    if eyebrow_candidates:
        print(f"\n" + "-" * 50)
        print("EYEBROW/EYE CANDIDATES:")
        print("-" * 50)

        for comp in eyebrow_candidates:
            print(f"\n{comp.name}:")
            print(f"  Path: {comp.path}")
            print(f"  Type: {type(comp).__name__}")

            # Check if it's a geometry COMP
            if hasattr(comp, 'children'):
                print(f"  Children:")
                for c in comp.children:
                    print(f"    - {c.name} ({type(c).__name__})")

            # Check for transform parameters
            if hasattr(comp, 'par'):
                # Check translate
                if hasattr(comp.par, 'ty'):
                    print(f"  Transform Y (ty): {comp.par.ty.eval()}")
                    print(f"  ty mode: {comp.par.ty.mode}")

print("\n" + "=" * 70 + "\n")
