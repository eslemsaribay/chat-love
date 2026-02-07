# Explore Eyelid Options
# ======================
# Find available eye data and eyelash COMP structure
#
# exec(open(project.folder + '/explore_eyelids.py').read())

print("\n" + "=" * 70)
print("EYELID EXPLORATION")
print("=" * 70)

EYELASH_PATH = '/project1/luna_container/Luna/Zenna_eyelashes02'
BLENDSHAPES_CHOP = '/project1/blend_shapes'
FACE_POINTS_CHOP = '/project1/face_points'

# =============================================================================
# 1. Check eyelash COMP structure
# =============================================================================

print("\n[1] EYELASH COMP STRUCTURE")
print("-" * 50)

eyelash = op(EYELASH_PATH)
if eyelash is None:
    print(f"  ERROR: Eyelash not found at {EYELASH_PATH}")
else:
    print(f"  Path: {eyelash.path}")
    print(f"  Type: {type(eyelash).__name__}")

    print(f"\n  Children:")
    for child in eyelash.children:
        child_type = type(child).__name__
        print(f"    {child.name} ({child_type})")

# =============================================================================
# 2. Check eye-related blendshapes
# =============================================================================

print("\n[2] EYE-RELATED BLENDSHAPES")
print("-" * 50)

blend = op(BLENDSHAPES_CHOP)
if blend is None:
    print(f"  ERROR: Blendshapes not found at {BLENDSHAPES_CHOP}")
else:
    print(f"  Total channels: {blend.numChans}")
    print(f"\n  Eye-related channels:")

    eye_chans = []
    for i in range(blend.numChans):
        chan = blend.chan(i)
        name_lower = chan.name.lower()
        if any(kw in name_lower for kw in ['eye', 'blink', 'squint', 'wink']):
            eye_chans.append((chan.name, chan.eval()))
            print(f"    {chan.name}: {chan.eval():.4f}")

    if not eye_chans:
        print("    (none found)")

# =============================================================================
# 3. Check eye landmarks in face_points
# =============================================================================

print("\n[3] EYE LANDMARKS (from MediaPipe)")
print("-" * 50)

# MediaPipe eye landmark indices
# Left eye: 33, 133, 160, 159, 158, 144, 145, 153
# Right eye: 362, 263, 387, 386, 385, 373, 374, 380
# Upper eyelid: 159 (left), 386 (right)
# Lower eyelid: 145 (left), 374 (right)

LEFT_UPPER = 159
LEFT_LOWER = 145
RIGHT_UPPER = 386
RIGHT_LOWER = 374

face_points = op(FACE_POINTS_CHOP)
if face_points is None:
    print(f"  ERROR: Face points not found at {FACE_POINTS_CHOP}")
else:
    print(f"  Total samples: {face_points.numSamples}")

    if face_points.numSamples >= 468:
        # Get eye positions
        def get_point(idx):
            try:
                x = face_points.chan('x')[idx]
                y = face_points.chan('y')[idx]
                z = face_points.chan('z')[idx]
                return (x, y, z)
            except:
                return None

        left_upper = get_point(LEFT_UPPER)
        left_lower = get_point(LEFT_LOWER)
        right_upper = get_point(RIGHT_UPPER)
        right_lower = get_point(RIGHT_LOWER)

        if left_upper and left_lower:
            left_gap = abs(left_upper[1] - left_lower[1])
            print(f"\n  Left eye:")
            print(f"    Upper lid (159): y={left_upper[1]:.4f}")
            print(f"    Lower lid (145): y={left_lower[1]:.4f}")
            print(f"    Gap (openness): {left_gap:.4f}")

        if right_upper and right_lower:
            right_gap = abs(right_upper[1] - right_lower[1])
            print(f"\n  Right eye:")
            print(f"    Upper lid (386): y={right_upper[1]:.4f}")
            print(f"    Lower lid (374): y={right_lower[1]:.4f}")
            print(f"    Gap (openness): {right_gap:.4f}")
    else:
        print(f"  Not enough samples for eye landmarks")

# =============================================================================
# 4. Test eyelash Transform POP approach
# =============================================================================

print("\n[4] PROPOSED SOLUTION")
print("-" * 50)

print("""
APPROACH: Use Transform POP on eyelash mesh

Since the eyelash mesh covers upper lashes, we can simulate "closing"
by scaling/translating the mesh:

Option A - Scale Y (compress vertically):
  When eyeBlinkLeft/Right = 1.0, scale sy to ~0.3
  This flattens the lashes against the face

Option B - Translate Y (move down):
  When eyeBlinkLeft/Right = 1.0, translate ty down
  This moves upper lashes toward lower lashes

Option C - Combine scale + translate:
  Scale down AND translate for more realistic effect

The blendshapes eyeBlinkLeft/eyeBlinkRight are ideal inputs
as they're already 0-1 normalized (0=open, 1=closed)
""")

# =============================================================================
# 5. Quick test - set eyelash scale manually
# =============================================================================

print("\n[5] MANUAL TEST")
print("-" * 50)

if eyelash:
    deform_pop = eyelash.op('deform')
    if deform_pop:
        print(f"  Found deform POP: {deform_pop.path}")
        print(f"  Current sy (if available): checking...")

        # Check if there's already a transform POP
        transform_pop = eyelash.op('eyelid_close')
        if transform_pop:
            print(f"  Existing eyelid_close POP found")
        else:
            print(f"  No eyelid_close POP yet (will be created by setup)")
    else:
        print(f"  No deform POP found in eyelash COMP")

print("\n" + "=" * 70)
print("EXPLORATION COMPLETE")
print("=" * 70)
print("""
RECOMMENDATION:
1. Use eyeBlinkLeft + eyeBlinkRight blendshapes (average them)
2. Add Transform POP to eyelash COMP
3. Link sy (scale Y) to: 1.0 - (blink * 0.7)
   This scales from 1.0 (open) to 0.3 (closed)
4. Optionally add small ty offset when closing

Run setup_head_tracking.py after implementing eyelid support.
""")
print("=" * 70 + "\n")
