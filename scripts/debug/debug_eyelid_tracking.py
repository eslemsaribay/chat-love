# Debug Eyelid Tracking
# =====================
# Check what values are being produced and Transform POP state
#
# exec(open(project.folder + '/debug_eyelid_tracking.py').read())

print("\n" + "=" * 70)
print("EYELID TRACKING DEBUG")
print("=" * 70)

BLENDSHAPES_CHOP = '/project1/blend_shapes'
HEAD_POSE_PATH = '/project1/luna_head_pose'
EYELASH_PATH = '/project1/luna_container/Luna/Zenna_eyelashes02'

# =============================================================================
# 1. Check blink blendshape values
# =============================================================================

print("\n[1] BLINK BLENDSHAPE VALUES")
print("-" * 50)

blend = op(BLENDSHAPES_CHOP)
if blend is None:
    print(f"  ERROR: Blendshapes CHOP not found at {BLENDSHAPES_CHOP}")
else:
    print(f"  Path: {blend.path}")
    print(f"  Channels: {blend.numChans}")

    # Find blink channels
    blink_left = None
    blink_right = None

    for i in range(blend.numChans):
        chan = blend.chan(i)
        if chan.name == 'eyeBlinkLeft':
            blink_left = chan.eval()
            print(f"  eyeBlinkLeft: {blink_left:.4f}")
        elif chan.name == 'eyeBlinkRight':
            blink_right = chan.eval()
            print(f"  eyeBlinkRight: {blink_right:.4f}")

    if blink_left is None:
        print(f"  WARNING: eyeBlinkLeft channel NOT FOUND")
    if blink_right is None:
        print(f"  WARNING: eyeBlinkRight channel NOT FOUND")

    if blink_left is not None and blink_right is not None:
        blink_avg = (blink_left + blink_right) / 2
        print(f"\n  Blink average: {blink_avg:.4f}")

        EYELID_DROP = 0.15
        EYELID_POWER = 3.0
        blink_curved = blink_avg ** EYELID_POWER
        eyelid_raw = -blink_curved * EYELID_DROP
        print(f"  Expected eyelid_ty: {eyelid_raw:.6f}")

# =============================================================================
# 2. Check head_pose CHOP eyelid_ty value
# =============================================================================

print("\n[2] HEAD POSE CHOP - EYELID_TY VALUE")
print("-" * 50)

head_pose = op(HEAD_POSE_PATH)
if head_pose is None:
    print(f"  ERROR: Head pose CHOP not found at {HEAD_POSE_PATH}")
else:
    print(f"  Path: {head_pose.path}")

    # Check all channels
    for i in range(head_pose.numChans):
        chan = head_pose.chan(i)
        print(f"    [{i}] {chan.name}: {chan.eval():.6f}")

    # Check specifically for eyelid_ty
    eyelid_chan = head_pose['eyelid_ty']
    if eyelid_chan:
        print(f"\n  eyelid_ty channel value: {eyelid_chan.eval():.6f}")
    else:
        print(f"\n  WARNING: eyelid_ty channel NOT FOUND in CHOP")

# =============================================================================
# 3. Check Transform POP state
# =============================================================================

print("\n[3] TRANSFORM POP STATE")
print("-" * 50)

eyelash = op(EYELASH_PATH)
if eyelash is None:
    print(f"  ERROR: Eyelash not found at {EYELASH_PATH}")
else:
    print(f"  Eyelash COMP: {eyelash.path}")

    # Check for eyelid_close Transform POP
    eyelid_pop = eyelash.op('eyelid_close')
    if eyelid_pop is None:
        print(f"  ERROR: eyelid_close Transform POP not found!")
    else:
        print(f"  Transform POP: {eyelid_pop.path}")
        print(f"  Type: {type(eyelid_pop).__name__}")

        # Check display/render flags
        print(f"\n  Display: {eyelid_pop.display}")
        print(f"  Render: {eyelid_pop.render}")

        # Check all transform parameters
        print(f"\n  Transform parameters:")
        for p in ['tx', 'ty', 'tz', 'rx', 'ry', 'rz', 'sx', 'sy', 'sz', 'px', 'py', 'pz']:
            par = getattr(eyelid_pop.par, p, None)
            if par:
                mode = str(par.mode).split('.')[-1]
                val = par.eval()
                expr = f" expr='{par.expr}'" if par.mode == ParMode.EXPRESSION else ""
                print(f"    {p}: {val:.6f} (mode: {mode}){expr}")

        # Test the expression directly
        if eyelid_pop.par.ty.mode == ParMode.EXPRESSION:
            expr = eyelid_pop.par.ty.expr
            print(f"\n  Testing ty expression: {expr}")
            try:
                result = eval(expr)
                print(f"  Expression evaluates to: {result:.6f}")
            except Exception as e:
                print(f"  Expression ERROR: {e}")

    # Also check deform POP
    deform_pop = eyelash.op('deform')
    if deform_pop:
        print(f"\n  Deform POP: {deform_pop.path}")
        print(f"  Deform display: {deform_pop.display}")
        print(f"  Deform render: {deform_pop.render}")

# =============================================================================
# 4. Check if Execute DAT is active
# =============================================================================

print("\n[4] EXECUTE DAT STATUS")
print("-" * 50)

exec_dat = op('/project1/luna_face_exec')
if exec_dat is None:
    print(f"  ERROR: Execute DAT not found at /project1/luna_face_exec")
else:
    print(f"  Path: {exec_dat.path}")
    print(f"  Active: {exec_dat.par.active.eval()}")
    print(f"  Frame Start enabled: {exec_dat.par.framestart.eval()}")

# =============================================================================
# 5. Manual test - set ty directly
# =============================================================================

print("\n[5] MANUAL TEST - SET TY DIRECTLY")
print("-" * 50)

if eyelid_pop:
    # Store current mode
    orig_mode = eyelid_pop.par.ty.mode
    orig_expr = eyelid_pop.par.ty.expr if orig_mode == ParMode.EXPRESSION else None

    # Set to constant and move
    eyelid_pop.par.ty.mode = ParMode.CONSTANT
    eyelid_pop.par.ty.val = -0.1  # Negative = move down

    print(f"  Set ty to -0.1 (CONSTANT mode)")
    print(f"  -> If eyelashes moved DOWN, Transform POP is working")
    print(f"  -> If they didn't move, there's a different issue")

    print(f"\n  To restore expression:")
    print(f"  op('{eyelid_pop.path}').par.ty.mode = ParMode.EXPRESSION")
    print(f"  op('{eyelid_pop.path}').par.ty.expr = \"{orig_expr}\"")

print("\n" + "=" * 70)
print("DEBUG COMPLETE")
print("=" * 70)
print("""
If eyelashes moved with manual ty=-0.1:
  -> Transform POP works, issue is with the value being calculated/passed
  -> Check: Is Execute DAT active? Is blendshape channel named correctly?

If eyelashes did NOT move:
  -> Transform POP not set as display/render output, or
  -> There's something overriding the Transform POP output
""")
print("=" * 70 + "\n")
