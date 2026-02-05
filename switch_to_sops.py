# Switch FBX from POPs to SOPs
# =============================
# This will rebuild the FBX COMP with SOPs instead of POPs,
# enabling Script SOP-based deformation.
#
# WARNING: This rebuilds the entire FBX network!
# Make sure to save your project first.
#
# exec(open(project.folder + '/switch_to_sops.py').read())

print("\n" + "=" * 70)
print("SWITCHING FBX FROM POPs TO SOPs")
print("=" * 70)

FBX_PATH = '/project1/luna_container/Luna'

fbx = op(FBX_PATH)
if fbx is None:
    print(f"ERROR: FBX COMP not found at {FBX_PATH}")
    raise SystemExit

# Check current setting
current_pops = fbx.par.pops.eval()
print(f"\n[1] Current pops setting: {current_pops}")

if not current_pops:
    print("  Already using SOPs! No change needed.")
else:
    print("\n[2] Switching to SOPs...")
    print("  Setting fbx.par.pops = False")
    fbx.par.pops = False

    print("\n[3] Triggering reimport...")
    print("  This will rebuild all geometry operators as SOPs.")

    # Trigger reimport
    if hasattr(fbx.par, 'imp'):
        fbx.par.imp.pulse()
        print("  Pulsed 'imp' (import) parameter")
    else:
        print("  WARNING: Could not find import pulse parameter")
        print("  You may need to manually click 'Import' on the FBX COMP")

    print("\n[4] Verifying change...")

    # Wait a moment for rebuild
    import time
    time.sleep(0.5)

    # Check the body mesh to see if it's now a SOP
    body = op('/project1/luna_container/Luna/Zenna_body')
    if body:
        mesh = body.op('mesh')
        deform = body.op('deform')

        print(f"\n  Zenna_body children:")
        for child in body.children:
            print(f"    {child.name} ({type(child).__name__})")

        if mesh:
            print(f"\n  mesh type: {type(mesh).__name__}")
            if 'SOP' in type(mesh).__name__:
                print("  SUCCESS: mesh is now a SOP!")
            else:
                print("  Still a POP - rebuild may not have completed yet")

        if deform:
            print(f"  deform type: {type(deform).__name__}")

print("\n" + "=" * 70)
print("NEXT STEPS")
print("=" * 70)
print("""
If the switch was successful (mesh is now a SOP):
  1. Run explore_body_mesh.py again to verify geometry access
  2. Then run the mouth deformation setup

If still showing POPs:
  1. Manually open the FBX COMP parameters
  2. Find 'POPs' or 'Use POPs' and set it to OFF
  3. Click 'Import' to rebuild
  4. Re-run this script to verify

Note: GPU Direct acceleration is disabled when using SOPs.
This may slightly impact performance but enables Script SOP deformation.
""")
print("=" * 70 + "\n")
