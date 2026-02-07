# Debug Eyebrow Setup
# ====================
# Investigate eyebrow geometry state and positioning
#
# exec(open(project.folder + '/debug_eyebrows.py').read())

print("\n" + "=" * 70)
print("EYEBROW DEBUG")
print("=" * 70)

EYEBROW_PATH = '/project1/luna_container/Luna/Zenna_eyebrow006'
EYELASH_PATH = '/project1/luna_container/Luna/Zenna_eyelashes02'
HEAD_POSE_PATH = '/project1/luna_head_pose'
LUNA_PATH = '/project1/luna_container/Luna'

# =============================================================================
# 1. Check eyebrow geometry
# =============================================================================

print("\n[1] EYEBROW GEOMETRY STATE")
print("-" * 50)

eyebrow = op(EYEBROW_PATH)
if eyebrow is None:
    print(f"  ERROR: Eyebrow not found at {EYEBROW_PATH}")
else:
    print(f"  Path: {eyebrow.path}")
    print(f"  Type: {type(eyebrow).__name__}")

    # Check transform parameters
    print(f"\n  Transform parameters:")
    print(f"    tx: {eyebrow.par.tx.eval():.4f} (mode: {eyebrow.par.tx.mode})")
    print(f"    ty: {eyebrow.par.ty.eval():.4f} (mode: {eyebrow.par.ty.mode})")
    print(f"    tz: {eyebrow.par.tz.eval():.4f} (mode: {eyebrow.par.tz.mode})")
    print(f"    rx: {eyebrow.par.rx.eval():.4f} (mode: {eyebrow.par.rx.mode})")
    print(f"    ry: {eyebrow.par.ry.eval():.4f} (mode: {eyebrow.par.ry.mode})")
    print(f"    rz: {eyebrow.par.rz.eval():.4f} (mode: {eyebrow.par.rz.mode})")
    print(f"    sx: {eyebrow.par.sx.eval():.4f}")
    print(f"    sy: {eyebrow.par.sy.eval():.4f}")
    print(f"    sz: {eyebrow.par.sz.eval():.4f}")

    # Check if ty has expression
    if eyebrow.par.ty.mode == ParMode.EXPRESSION:
        print(f"\n  ty expression: {eyebrow.par.ty.expr}")
        try:
            val = eyebrow.par.ty.eval()
            print(f"  ty evaluated value: {val}")
        except Exception as e:
            print(f"  ty evaluation ERROR: {e}")

    # Check geometry
    null_out = eyebrow.op('null')
    if null_out:
        print(f"\n  Geometry (from null):")
        print(f"    Points: {null_out.numPoints}")
        if null_out.numPoints > 0:
            # Get bounds
            pts = null_out.points
            x_vals = [p.P[0] for p in pts]
            y_vals = [p.P[1] for p in pts]
            z_vals = [p.P[2] for p in pts]
            print(f"    X range: {min(x_vals):.4f} to {max(x_vals):.4f}")
            print(f"    Y range: {min(y_vals):.4f} to {max(y_vals):.4f}")
            print(f"    Z range: {min(z_vals):.4f} to {max(z_vals):.4f}")

# =============================================================================
# 2. Check eyelashes
# =============================================================================

print("\n[2] EYELASH GEOMETRY STATE")
print("-" * 50)

eyelash = op(EYELASH_PATH)
if eyelash is None:
    print(f"  ERROR: Eyelash not found at {EYELASH_PATH}")
else:
    print(f"  Path: {eyelash.path}")
    print(f"  Type: {type(eyelash).__name__}")

    print(f"\n  Transform parameters:")
    print(f"    tx: {eyelash.par.tx.eval():.4f} (mode: {eyelash.par.tx.mode})")
    print(f"    ty: {eyelash.par.ty.eval():.4f} (mode: {eyelash.par.ty.mode})")
    print(f"    tz: {eyelash.par.tz.eval():.4f} (mode: {eyelash.par.tz.mode})")

# =============================================================================
# 3. Check head_pose CHOP
# =============================================================================

print("\n[3] HEAD POSE CHOP STATE")
print("-" * 50)

head_pose = op(HEAD_POSE_PATH)
if head_pose is None:
    print(f"  ERROR: Head pose CHOP not found at {HEAD_POSE_PATH}")
else:
    print(f"  Path: {head_pose.path}")
    print(f"  Channels: {head_pose.numChans}")

    for i in range(head_pose.numChans):
        chan = head_pose.chan(i)
        print(f"    [{i}] {chan.name}: {chan.eval():.6f}")

# =============================================================================
# 4. Check Luna render settings
# =============================================================================

print("\n[4] LUNA RENDER CHECK")
print("-" * 50)

luna = op(LUNA_PATH)
if luna:
    # Check if eyebrow is a child
    eyebrow_child = luna.op('Zenna_eyebrow006')
    if eyebrow_child:
        print(f"  Eyebrow is direct child of Luna: YES")
        print(f"  Eyebrow display: {eyebrow_child.par.display.eval() if hasattr(eyebrow_child.par, 'display') else 'N/A'}")
        print(f"  Eyebrow render: {eyebrow_child.par.render.eval() if hasattr(eyebrow_child.par, 'render') else 'N/A'}")
    else:
        print(f"  Eyebrow is direct child of Luna: NO")

# =============================================================================
# 5. Reset eyebrow to check original position
# =============================================================================

print("\n[5] RESET EYEBROW TO CONSTANT MODE")
print("-" * 50)

if eyebrow and eyebrow.par.ty.mode == ParMode.EXPRESSION:
    current_val = eyebrow.par.ty.eval()
    print(f"  Current ty value (from expression): {current_val:.6f}")

    # Temporarily reset to see original
    eyebrow.par.ty.mode = ParMode.CONSTANT
    eyebrow.par.ty.val = 0
    print(f"  Reset ty to 0 (CONSTANT mode)")
    print(f"  Check if eyebrows are visible now!")
else:
    print(f"  Eyebrow ty is already in CONSTANT mode or not found")

# =============================================================================
# 6. List all geometry COMPs in Luna with their visibility
# =============================================================================

print("\n[6] ALL GEOMETRY COMPS IN LUNA")
print("-" * 50)

if luna:
    geo_comps = [c for c in luna.children if 'geometryCOMP' in type(c).__name__]
    print(f"  Found {len(geo_comps)} geometry COMPs:")
    for gc in geo_comps:
        disp = gc.par.display.eval() if hasattr(gc.par, 'display') else '?'
        rend = gc.par.render.eval() if hasattr(gc.par, 'render') else '?'
        ty_val = gc.par.ty.eval() if hasattr(gc.par, 'ty') else '?'
        ty_mode = gc.par.ty.mode if hasattr(gc.par, 'ty') else '?'
        print(f"    {gc.name}: display={disp}, render={rend}, ty={ty_val} ({ty_mode})")

print("\n" + "=" * 70)
print("DEBUG COMPLETE")
print("=" * 70)
print("""
If eyebrows are now visible after reset:
  The issue was the expression producing wrong values.

If eyebrows are still not visible:
  The issue is elsewhere (render settings, material, or geometry).

To re-enable tracking after fixing:
  exec(open(project.folder + '/setup_head_tracking.py').read())
""")
print("=" * 70 + "\n")
