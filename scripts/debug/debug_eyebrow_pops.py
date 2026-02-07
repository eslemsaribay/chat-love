# Debug Eyebrow POPs Structure
# =============================
# Investigate eyebrow COMP structure after POP import
#
# exec(open(project.folder + '/debug_eyebrow_pops.py').read())

print("\n" + "=" * 70)
print("EYEBROW POPs DEBUG")
print("=" * 70)

EYEBROW_PATH = '/project1/luna_container/Luna/Zenna_eyebrow006'
HEAD_POSE_PATH = '/project1/luna_head_pose'

# =============================================================================
# 1. Check eyebrow COMP structure
# =============================================================================

print("\n[1] EYEBROW COMP STRUCTURE")
print("-" * 50)

eyebrow = op(EYEBROW_PATH)
if eyebrow is None:
    print(f"  ERROR: Eyebrow not found at {EYEBROW_PATH}")
else:
    print(f"  Path: {eyebrow.path}")
    print(f"  Type: {type(eyebrow).__name__}")
    print(f"  Family: {eyebrow.family}")

    # Check children
    print(f"\n  Children ({len(eyebrow.children)}):")
    for child in eyebrow.children:
        child_type = type(child).__name__
        family = child.family if hasattr(child, 'family') else 'N/A'
        print(f"    {child.name} ({child_type}, family: {family})")

    # Check transform parameters
    print(f"\n  Transform parameters:")
    for p in ['tx', 'ty', 'tz', 'rx', 'ry', 'rz', 'sx', 'sy', 'sz', 'px', 'py', 'pz']:
        par = getattr(eyebrow.par, p, None)
        if par:
            mode_str = str(par.mode).split('.')[-1] if hasattr(par, 'mode') else 'N/A'
            expr_str = f" expr='{par.expr}'" if par.mode == ParMode.EXPRESSION else ""
            print(f"    {p}: {par.eval():.6f} (mode: {mode_str}){expr_str}")

# =============================================================================
# 2. Check if there's a deform/skinning operator
# =============================================================================

print("\n[2] LOOKING FOR DEFORMATION OPERATORS")
print("-" * 50)

if eyebrow:
    # Look for POPs or SOPs that might be doing skinning
    for child in eyebrow.children:
        child_type = type(child).__name__
        print(f"\n  {child.name} ({child_type}):")

        # Check if it has inputs
        if hasattr(child, 'inputs') and child.inputs:
            print(f"    Inputs: {[i.name for i in child.inputs]}")

        # Check if it's a POP
        if 'POP' in child_type or child.family == 'POP':
            print(f"    -> This is a POP!")
            # Check for parameters that might control position
            if hasattr(child, 'par'):
                for pname in ['tx', 'ty', 'tz', 'px', 'py', 'pz']:
                    par = getattr(child.par, pname, None)
                    if par:
                        print(f"    {pname}: {par.eval()}")

# =============================================================================
# 3. Check head_pose CHOP values
# =============================================================================

print("\n[3] HEAD POSE CHOP VALUES")
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
# 4. Test manual ty change
# =============================================================================

print("\n[4] TESTING MANUAL TY CHANGE")
print("-" * 50)

if eyebrow:
    # Store current mode
    orig_mode = eyebrow.par.ty.mode
    orig_val = eyebrow.par.ty.eval()
    print(f"  Original ty: {orig_val:.6f} (mode: {orig_mode})")

    # Try setting to constant mode and change value
    eyebrow.par.ty.mode = ParMode.CONSTANT
    eyebrow.par.ty.val = 0.1  # Large value to see effect

    import time
    time.sleep(0.1)  # Wait for update

    new_val = eyebrow.par.ty.eval()
    print(f"  After setting ty=0.1: {new_val:.6f}")
    print(f"  -> If eyebrow moved up, ty works!")
    print(f"  -> If eyebrow didn't move, something else controls position")

    # Keep it at 0.1 so user can visually check
    print(f"\n  NOTE: ty left at 0.1 for visual inspection")
    print(f"  Run this to restore: op('{EYEBROW_PATH}').par.ty.val = 0")

# =============================================================================
# 5. Check if there's a lookup CHOP or deform relationship
# =============================================================================

print("\n[5] CHECKING FOR EXTERNAL REFERENCES")
print("-" * 50)

if eyebrow:
    # Check if any parameters reference external operators
    transform_pars = ['tx', 'ty', 'tz', 'rx', 'ry', 'rz']
    for pname in transform_pars:
        par = getattr(eyebrow.par, pname, None)
        if par and par.mode == ParMode.EXPRESSION:
            print(f"  {pname} expression: {par.expr}")
        elif par and par.mode != ParMode.CONSTANT:
            print(f"  {pname} mode: {par.mode}")

    # Check for lookupCHOP or other binding mechanisms
    for child in eyebrow.children:
        child_type = type(child).__name__
        if 'lookup' in child.name.lower() or 'CHOP' in child_type:
            print(f"  Found potential binding: {child.name} ({child_type})")

# =============================================================================
# 6. List all geometry COMPs in Luna to understand hierarchy
# =============================================================================

print("\n[6] LUNA HIERARCHY")
print("-" * 50)

luna = op('/project1/luna_container/Luna')
if luna:
    print(f"  Luna children:")
    for child in luna.children:
        child_type = type(child).__name__
        if 'geometryCOMP' in child_type or 'COMP' in child_type:
            # Check if transforms are expressions
            ty_info = ""
            if hasattr(child.par, 'ty'):
                ty_mode = str(child.par.ty.mode).split('.')[-1]
                ty_val = child.par.ty.eval()
                ty_info = f" ty={ty_val:.4f} ({ty_mode})"
            print(f"    {child.name} ({child_type}){ty_info}")

print("\n" + "=" * 70)
print("DEBUG COMPLETE")
print("=" * 70)
print("""
Check visually:
- If eyebrow moved up after ty=0.1, the COMP transform works
- If eyebrow didn't move, the position is controlled by internal POPs/deformation

To restore eyebrow ty:
  op('/project1/luna_container/Luna/Zenna_eyebrow006').par.ty.val = 0
""")
print("=" * 70 + "\n")
