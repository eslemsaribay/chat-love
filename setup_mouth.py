# Setup Mouth Deformation for Luna Model
# =======================================
# Single script to set up mouth deformation on the body mesh.
#
# Run in TouchDesigner:
#   exec(open(project.folder + '/setup_mouth.py').read())
#
# What this does:
#   1. Inserts a Script SOP between bonegroup and null in Zenna_body
#   2. Creates deformation script driven by MediaPipe blendshapes
#   3. Applies jaw open, lip movements, smile, pucker effects

print("\n" + "=" * 70)
print("MOUTH DEFORMATION SETUP")
print("=" * 70)

# =============================================================================
# CONFIGURATION
# =============================================================================

# Paths
BODY_PATH = '/project1/luna_container/Luna/Zenna_body'
BLENDSHAPES_CHOP = '/project1/blend_shapes'

# Mouth region bounds (from geometry analysis)
MOUTH_Y_MIN = 1.428
MOUTH_Y_MAX = 1.543
MOUTH_Z_MIN = 0.098
MOUTH_Z_MAX = 0.159
LIP_BOUNDARY_Y = 1.486

# Deformation scales (tweak these to adjust intensity)
JAW_SCALE = 0.02       # How much jaw opening moves lower lip down
LIP_UP_SCALE = 0.01    # Upper lip raise amount
LIP_DOWN_SCALE = 0.01  # Lower lip drop amount
SMILE_SCALE_Y = 0.008  # Smile corner lift
SMILE_SCALE_X = 0.005  # Smile corner spread
SMOOTHING = 0.7        # Temporal smoothing (0=none, 1=max)

# =============================================================================
# STEP 1: Validate paths
# =============================================================================

print("\n[1] Validating paths...")

container = op(BODY_PATH)
if container is None:
    print(f"  ERROR: Body mesh not found at {BODY_PATH}")
    print(f"  Make sure the Luna FBX is loaded.")
    raise SystemExit

mesh = container.op('mesh')
bonegroup = container.op('bonegroup')
null_out = container.op('null')

missing = []
if not mesh: missing.append('mesh')
if not bonegroup: missing.append('bonegroup')
if not null_out: missing.append('null')

if missing:
    print(f"  ERROR: Missing operators: {missing}")
    print(f"  Available operators in {container.name}:")
    for child in container.children:
        print(f"    - {child.name} ({type(child).__name__})")
    raise SystemExit

print(f"  Body mesh: {container.path}")
print(f"  Chain: mesh -> bonegroup -> null")

# Verify blendshapes
blend_chop = op(BLENDSHAPES_CHOP)
if blend_chop is None:
    print(f"  WARNING: Blendshapes CHOP not found at {BLENDSHAPES_CHOP}")
    print(f"  Mouth deformation will not animate until MediaPipe is running.")
else:
    print(f"  Blendshapes: {blend_chop.path} ({blend_chop.numChans} channels)")

# =============================================================================
# STEP 2: Clean up any previous setup
# =============================================================================

print("\n[2] Cleaning up previous setup...")

# Remove old operators
for name in ['face_deform', 'mouth_deform_script', 'face_out', 'in1']:
    old_op = container.op(name)
    if old_op:
        # Restore null connection before deleting
        if name == 'face_deform' and null_out:
            null_out.inputConnectors[0].connect(bonegroup)
        old_op.destroy()
        print(f"  Removed: {name}")

print(f"  Clean.")

# =============================================================================
# STEP 3: Create Script SOP
# =============================================================================

print("\n[3] Creating Script SOP...")

script_sop = container.create(scriptSOP, 'face_deform')
print(f"  Created: {script_sop.path}")

# Insert between bonegroup and null
script_sop.inputConnectors[0].connect(bonegroup)
null_out.inputConnectors[0].connect(script_sop)
print(f"  Connected: bonegroup -> face_deform -> null")

# Position in network
script_sop.nodeX = bonegroup.nodeX + 150
script_sop.nodeY = bonegroup.nodeY

# =============================================================================
# STEP 4: Create deformation script
# =============================================================================

print("\n[4] Creating deformation script...")

DEFORM_SCRIPT = '''# Mouth Deformation Script
# Driven by MediaPipe blendshapes

# Configuration (embedded from setup)
BLENDSHAPES_CHOP = "''' + BLENDSHAPES_CHOP + '''"
MOUTH_Y_MIN = ''' + str(MOUTH_Y_MIN) + '''
MOUTH_Y_MAX = ''' + str(MOUTH_Y_MAX) + '''
MOUTH_Z_MIN = ''' + str(MOUTH_Z_MIN) + '''
MOUTH_Z_MAX = ''' + str(MOUTH_Z_MAX) + '''
LIP_BOUNDARY_Y = ''' + str(LIP_BOUNDARY_Y) + '''
JAW_SCALE = ''' + str(JAW_SCALE) + '''
LIP_UP_SCALE = ''' + str(LIP_UP_SCALE) + '''
LIP_DOWN_SCALE = ''' + str(LIP_DOWN_SCALE) + '''
SMILE_SCALE_Y = ''' + str(SMILE_SCALE_Y) + '''
SMILE_SCALE_X = ''' + str(SMILE_SCALE_X) + '''
SMOOTHING = ''' + str(SMOOTHING) + '''


def onCook(scriptOP):
    # CRITICAL: Copy input geometry first
    scriptOP.clear()
    if not scriptOP.inputs or scriptOP.inputs[0].numPoints == 0:
        return
    scriptOP.copy(scriptOP.inputs[0])

    # Get blendshapes
    blend = op(BLENDSHAPES_CHOP)
    if not blend:
        return

    # Initialize state (using storage for persistence)
    if 'state' not in scriptOP.storage:
        scriptOP.storage['state'] = {
            'init': False,
            'rest': {},
            'mouth': [],
            'upper': [],
            'lower': [],
            'deltas': {}
        }

    s = scriptOP.storage['state']

    # First-time initialization: find mouth vertices
    if not s['init']:
        for pt in scriptOP.points:
            y, z = pt.P[1], pt.P[2]
            if MOUTH_Y_MIN <= y <= MOUTH_Y_MAX and MOUTH_Z_MIN <= z <= MOUTH_Z_MAX:
                idx = pt.index
                s['mouth'].append(idx)
                s['rest'][idx] = (pt.P[0], pt.P[1], pt.P[2])
                if y > LIP_BOUNDARY_Y:
                    s['upper'].append(idx)
                else:
                    s['lower'].append(idx)
        s['init'] = True
        print(f"[Mouth] Found {len(s['mouth'])} verts (upper:{len(s['upper'])}, lower:{len(s['lower'])})")

    # Read blendshapes (safe get)
    def get(name):
        try:
            c = blend[name]
            return c.eval() if c else 0.0
        except:
            return 0.0

    jaw = get('jawOpen')
    upperL = get('mouthUpperUpLeft')
    upperR = get('mouthUpperUpRight')
    lowerL = get('mouthLowerDownLeft')
    lowerR = get('mouthLowerDownRight')
    smileL = get('mouthSmileLeft')
    smileR = get('mouthSmileRight')
    pucker = get('mouthPucker')

    # Average L/R
    upper = (upperL + upperR) / 2
    lower = (lowerL + lowerR) / 2
    smile = (smileL + smileR) / 2

    # Mouth center X for smile spread
    if s['mouth']:
        cx = sum(s['rest'][i][0] for i in s['mouth']) / len(s['mouth'])
    else:
        cx = 0.0

    # Apply deformation
    for idx in s['mouth']:
        rx, ry, rz = s['rest'][idx]
        dx, dy, dz = 0.0, 0.0, 0.0

        # Jaw/lip Y movement
        if idx in s['lower']:
            dy = -jaw * JAW_SCALE - lower * LIP_DOWN_SCALE
        elif idx in s['upper']:
            dy = upper * LIP_UP_SCALE

        # Smile: corners lift and spread
        dist = abs(rx - cx)
        corner = min(1.0, dist / 0.05)
        dy += smile * SMILE_SCALE_Y * corner
        if rx > cx:
            dx += smile * SMILE_SCALE_X * corner
        else:
            dx -= smile * SMILE_SCALE_X * corner

        # Pucker: forward
        dz += pucker * 0.01

        # Smooth
        prev = s['deltas'].get(idx, (0, 0, 0))
        dx = prev[0] * SMOOTHING + dx * (1 - SMOOTHING)
        dy = prev[1] * SMOOTHING + dy * (1 - SMOOTHING)
        dz = prev[2] * SMOOTHING + dz * (1 - SMOOTHING)
        s['deltas'][idx] = (dx, dy, dz)

        # Apply
        scriptOP.points[idx].P = (rx + dx, ry + dy, rz + dz)
'''

script_dat = container.create(textDAT, 'mouth_deform_script')
script_dat.text = DEFORM_SCRIPT
script_dat.nodeX = script_sop.nodeX
script_dat.nodeY = script_sop.nodeY - 120

print(f"  Created: {script_dat.path}")

# Link script to SOP
script_sop.par.callbacks = script_dat.path
print(f"  Linked callbacks")

# =============================================================================
# STEP 5: Verify
# =============================================================================

print("\n[5] Verifying...")

script_sop.cook(force=True)

try:
    pts = script_sop.numPoints
    print(f"  Script SOP: {pts} points")

    if pts > 0:
        if 'state' in script_sop.storage and script_sop.storage['state']['init']:
            st = script_sop.storage['state']
            print(f"  Mouth vertices: {len(st['mouth'])}")
            print(f"  Upper lip: {len(st['upper'])}")
            print(f"  Lower lip: {len(st['lower'])}")
        else:
            print(f"  State will initialize on next cook")
    else:
        print(f"  WARNING: No geometry - check bonegroup input")
except Exception as e:
    print(f"  Error: {e}")

# =============================================================================
# DONE
# =============================================================================

print("\n" + "=" * 70)
print("SETUP COMPLETE")
print("=" * 70)
print(f"""
Chain: mesh -> bonegroup -> face_deform -> null

Blendshape mappings:
  jawOpen         -> lower lip/jaw moves down
  mouthUpperUp*   -> upper lip moves up
  mouthLowerDown* -> lower lip moves down
  mouthSmile*     -> corners lift and spread
  mouthPucker     -> lips move forward

To test: Make sure MediaPipe face tracking is running, then move your mouth.

To adjust intensity, edit the scales in {script_dat.path}:
  JAW_SCALE, LIP_UP_SCALE, LIP_DOWN_SCALE, SMILE_SCALE_Y, SMILE_SCALE_X
""")
print("=" * 70 + "\n")
