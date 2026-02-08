# Auto-Scale Luna Model Based on Face Distance
# =============================================
# Scales Luna model based on detected face size (proxy for distance)
#
# exec(open(project.folder + '/setup_auto_scale.py').read())

print("\n" + "=" * 70)
print("AUTO-SCALE SETUP")
print("=" * 70)

MEDIAPIPE_CHOP = '/project1/face_points'
LUNA_PATH = '/project1/luna_container/Luna'
CONTAINER_PATH = '/project1/luna_container'
HEAD_POSE_PATH = '/project1/luna_container/luna_head_pose'

# =============================================================================
# TUNING PARAMETERS
# =============================================================================

# Base scale when face is at "normal" distance (face height ~0.25 of frame)
BASE_SCALE = 1.5

# Reference face height (normalized 0-1) - calibrate this to your setup
# When face is this size, model will be at BASE_SCALE
REFERENCE_FACE_HEIGHT = 0.25

# Scale sensitivity - how much scale changes with face size (lower = less aggressive)
SCALE_SENSITIVITY = 0.4

# Smoothing for scale changes (0-1, higher = smoother)
SCALE_SMOOTH = 0.9

# Min/max scale limits
SCALE_MIN = 1.2
SCALE_MAX = 1.42

# Base Y position (negative = lower on screen)
BASE_TY = -0.5

# Vertical offset - moves model DOWN as it scales UP to keep it in frame
# ty = BASE_TY - (scale - BASE_SCALE) * TY_PER_SCALE
TY_PER_SCALE = 0.3

# =============================================================================
# SETUP
# =============================================================================

def setup_auto_scale():
    container = op(CONTAINER_PATH)
    mp = op(MEDIAPIPE_CHOP)
    luna = op(LUNA_PATH)
    head_pose = op(HEAD_POSE_PATH)

    if mp is None:
        print(f"ERROR: MediaPipe CHOP not found at {MEDIAPIPE_CHOP}")
        return False

    if luna is None:
        print(f"ERROR: Luna not found at {LUNA_PATH}")
        return False

    if head_pose is None:
        print(f"ERROR: Head pose CHOP not found at {HEAD_POSE_PATH}")
        print(f"       Run setup_head_tracking.py first!")
        return False

    print(f"[OK] MediaPipe: {mp.path}")
    print(f"[OK] Luna: {luna.path}")
    print(f"[OK] Head pose: {head_pose.path}")

    # -------------------------------------------------------------------------
    # Add scale channel to head_pose Constant CHOP
    # -------------------------------------------------------------------------
    print("\n[1] Adding scale channel to luna_head_pose...")

    # Check if channel already exists
    existing_chans = head_pose.numChans
    scale_chan_exists = False

    for i in range(existing_chans):
        if head_pose.chan(i).name == 'model_scale':
            scale_chan_exists = True
            break

    if not scale_chan_exists:
        # Add new channel (find next available slot)
        next_slot = existing_chans
        setattr(head_pose.par, f'name{next_slot}', 'model_scale')
        setattr(head_pose.par, f'value{next_slot}', BASE_SCALE)
        print(f"    Added channel 'model_scale' at slot {next_slot}")
    else:
        print(f"    Channel 'model_scale' already exists")

    # Check if ty channel exists
    ty_chan_exists = False
    for i in range(head_pose.numChans):
        if head_pose.chan(i).name == 'model_ty':
            ty_chan_exists = True
            break

    if not ty_chan_exists:
        next_slot = head_pose.numChans
        setattr(head_pose.par, f'name{next_slot}', 'model_ty')
        setattr(head_pose.par, f'value{next_slot}', 0.0)
        print(f"    Added channel 'model_ty' at slot {next_slot}")
    else:
        print(f"    Channel 'model_ty' already exists")

    # -------------------------------------------------------------------------
    # Update Execute DAT to calculate scale
    # -------------------------------------------------------------------------
    print("\n[2] Updating Execute DAT with scale calculation...")

    exec_dat = op(CONTAINER_PATH + '/luna_face_exec')
    if exec_dat is None:
        print(f"    ERROR: Execute DAT not found")
        return False

    # Read current code and inject scale calculation
    current_code = exec_dat.text

    # Remove old scale code if exists, then inject new
    if 'AUTO-SCALE based on face size' in current_code:
        # Remove old scale code block
        start_marker = "    # -------------------------------------------------------------------------\n    # AUTO-SCALE based on face size"
        end_marker = "# Required callback stubs"
        start_idx = current_code.find(start_marker)
        end_idx = current_code.find(end_marker)
        if start_idx != -1 and end_idx != -1:
            current_code = current_code[:start_idx] + current_code[end_idx:]
            print(f"    Removed old scale code")

    if True:  # Always inject fresh code
        # Find the end of onFrameStart function and inject scale code
        scale_code = f'''
    # -------------------------------------------------------------------------
    # AUTO-SCALE based on face size
    # -------------------------------------------------------------------------
    # Use face height (forehead to chin) as proxy for distance
    FOREHEAD_IDX = 10
    CHIN_IDX = 152
    BASE_TY = {BASE_TY}
    TY_PER_SCALE = {TY_PER_SCALE}

    forehead = lm(FOREHEAD_IDX)
    chin_pt = lm(CHIN_IDX)

    if forehead and chin_pt:
        # Face height in normalized coordinates (0-1)
        face_height = abs(forehead[1] - chin_pt[1])

        # Calculate scale: larger face = larger scale (with reduced sensitivity)
        scale_factor = face_height / {REFERENCE_FACE_HEIGHT}
        target_scale = {BASE_SCALE} * (scale_factor ** {SCALE_SENSITIVITY})

        # Clamp to limits
        target_scale = max({SCALE_MIN}, min({SCALE_MAX}, target_scale))

        # Get previous scale for smoothing
        prev_scale = state.get('prev_scale', {BASE_SCALE})

        # Smooth
        new_scale = prev_scale * {SCALE_SMOOTH} + target_scale * (1 - {SCALE_SMOOTH})
        state['prev_scale'] = new_scale

        # Calculate ty offset: base position + move DOWN as scale increases
        target_ty = BASE_TY - (new_scale - {BASE_SCALE}) * TY_PER_SCALE
        prev_ty = state.get('prev_model_ty', 0.0)
        new_ty = prev_ty * {SCALE_SMOOTH} + target_ty * (1 - {SCALE_SMOOTH})
        state['prev_model_ty'] = new_ty

        # Output scale and ty (find the channel slots)
        for i in range(15):
            name_par = getattr(hp.par, f'name{{i}}', None)
            if name_par:
                chan_name = name_par.eval()
                if chan_name == 'model_scale':
                    setattr(hp.par, f'value{{i}}', new_scale)
                elif chan_name == 'model_ty':
                    setattr(hp.par, f'value{{i}}', new_ty)
'''

        # Insert before the "Required callback stubs" section
        marker = "# Required callback stubs"
        if marker in current_code:
            new_code = current_code.replace(marker, scale_code + "\n" + marker)
            exec_dat.text = new_code
            print(f"    Injected scale calculation into Execute DAT")
        else:
            print(f"    WARNING: Could not find insertion point in Execute DAT")
            print(f"             You may need to add scale code manually")

    # -------------------------------------------------------------------------
    # Link Luna scale to head_pose channel
    # -------------------------------------------------------------------------
    print("\n[3] Linking Luna scale and position to channels...")

    luna.par.sx.mode = ParMode.EXPRESSION
    luna.par.sx.expr = f"op('{HEAD_POSE_PATH}')['model_scale']"

    luna.par.sy.mode = ParMode.EXPRESSION
    luna.par.sy.expr = f"op('{HEAD_POSE_PATH}')['model_scale']"

    luna.par.sz.mode = ParMode.EXPRESSION
    luna.par.sz.expr = f"op('{HEAD_POSE_PATH}')['model_scale']"

    luna.par.ty.mode = ParMode.EXPRESSION
    luna.par.ty.expr = f"op('{HEAD_POSE_PATH}')['model_ty']"

    print(f"    sx -> luna_head_pose['model_scale']")
    print(f"    sy -> luna_head_pose['model_scale']")
    print(f"    sz -> luna_head_pose['model_scale']")
    print(f"    ty -> luna_head_pose['model_ty']")

    # -------------------------------------------------------------------------
    # Done
    # -------------------------------------------------------------------------
    print("\n" + "=" * 70)
    print("AUTO-SCALE SETUP COMPLETE")
    print("=" * 70)
    print(f"""
Luna model will now auto-scale based on face distance:
  - Move closer to camera → model gets larger AND moves down
  - Move further from camera → model gets smaller AND moves up

Tuning parameters (edit this script):
  BASE_SCALE = {BASE_SCALE}           # Scale at reference distance
  REFERENCE_FACE_HEIGHT = {REFERENCE_FACE_HEIGHT}  # Face height at reference distance
  SCALE_SENSITIVITY = {SCALE_SENSITIVITY}      # How responsive (lower = less aggressive)
  SCALE_SMOOTH = {SCALE_SMOOTH}           # Smoothing (higher = smoother)
  SCALE_MIN = {SCALE_MIN}             # Minimum scale
  SCALE_MAX = {SCALE_MAX}             # Maximum scale
  BASE_TY = {BASE_TY}            # Base Y position (negative = lower)
  TY_PER_SCALE = {TY_PER_SCALE}          # How much to move down per scale increase

To disable auto-scale:
  luna = op('{LUNA_PATH}')
  luna.par.sx.mode = ParMode.CONSTANT
  luna.par.sy.mode = ParMode.CONSTANT
  luna.par.sz.mode = ParMode.CONSTANT
  luna.par.ty.mode = ParMode.CONSTANT
  luna.par.sx = 1.5
  luna.par.sy = 1.5
  luna.par.sz = 1.5
  luna.par.ty = 0
""")
    return True


# Run setup
setup_auto_scale()
