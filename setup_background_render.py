"""
TouchDesigner Script: Setup Background Render Pipeline
Run this script in TouchDesigner's Text Port or a DAT Execute

This creates a separate render pipeline for the background.jpeg image.
"""

def setup_background_render():
    """Create a complete background render pipeline"""

    # Get the project container
    project = op('/project1')

    # Check if background_render already exists, if so, delete it
    if project.op('background_render'):
        print("Removing existing background_render...")
        project.op('background_render').destroy()

    print("Creating background render pipeline...")

    # Create a container for the background render pipeline
    bg_container = project.create(containerCOMP, 'background_render')
    bg_container.nodeX = 500
    bg_container.nodeY = 0
    bg_container.color = (0.3, 0.5, 0.7)  # Blue tint for easy identification
    bg_container.comment = "Background Image Render Pipeline"

    # Create Movie File In TOP to load the background image
    bg_image = bg_container.create(moviefileinTOP, 'bg_image')
    bg_image.par.file = '../resources/background.jpeg'
    bg_image.par.play = False  # Static image
    bg_image.par.cuelength = 1  # Load just one frame

    # Create a Camera for the background scene
    bg_camera = bg_container.create(cameraCOMP, 'bg_camera')
    bg_camera.par.tx = 0
    bg_camera.par.ty = 0
    bg_camera.par.tz = 5  # Move camera back to see the plane
    bg_camera.par.fov = 40

    # Create a Geometry COMP to display the background on a plane
    bg_geo = bg_container.create(geometryCOMP, 'bg_geometry')

    # Create a Grid SOP inside the geometry
    grid = bg_geo.create(gridSOP, 'grid')
    grid.par.rows = 1
    grid.par.cols = 1
    grid.par.sizex = 16  # 16:9 aspect ratio
    grid.par.sizey = 9

    # Create a Null SOP to output the grid
    null_out = bg_geo.create(nullSOP, 'OUT')
    null_out.setInput(0, grid)
    bg_geo.par.display = True

    # Create a Phong MAT for the background (simpler than PBR)
    bg_mat = bg_container.create(phongMAT, 'bg_material')
    bg_mat.par.colormap = bg_image
    bg_mat.par.diffr = 1
    bg_mat.par.diffg = 1
    bg_mat.par.diffb = 1

    # Assign material to geometry
    bg_geo.par.mat = bg_mat

    # Create a Light for the scene
    bg_light = bg_container.create(lightCOMP, 'bg_light')
    bg_light.par.lighttype = 'point'
    bg_light.par.tx = 0
    bg_light.par.ty = 2
    bg_light.par.tz = 3
    bg_light.par.dimmer = 1

    # Create the Render TOP
    bg_render = bg_container.create(renderTOP, 'bg_render')
    bg_render.par.camera = bg_camera
    bg_render.par.geometry = bg_geo
    bg_render.par.light1 = bg_light
    bg_render.par.resx = 1920
    bg_render.par.resy = 1080
    bg_render.par.bgcolorr = 0
    bg_render.par.bgcolorg = 0
    bg_render.par.bgcolorb = 0

    # Create output NULL TOP for easy reference
    output_null = bg_container.create(nullTOP, 'OUT')
    output_null.setInput(0, bg_render)

    # Organize the network layout
    bg_image.nodeX = -300
    bg_image.nodeY = 200
    bg_image.color = (0.8, 0.4, 0.4)  # Red tint for image source

    bg_camera.nodeX = 0
    bg_camera.nodeY = 200
    bg_camera.color = (0.4, 0.8, 0.4)  # Green tint for camera

    bg_light.nodeX = 100
    bg_light.nodeY = 200
    bg_light.color = (0.9, 0.9, 0.4)  # Yellow tint for light

    bg_mat.nodeX = -300
    bg_mat.nodeY = 100

    bg_geo.nodeX = -100
    bg_geo.nodeY = 100

    bg_render.nodeX = 0
    bg_render.nodeY = 0

    output_null.nodeX = 0
    output_null.nodeY = -100
    output_null.color = (0.4, 0.4, 0.8)  # Blue tint for output

    print("✓ Background render pipeline created successfully!")
    print(f"✓ Container: {bg_container.path}")
    print(f"✓ Background image: {bg_image.path}")
    print(f"✓ Render output: {output_null.path}")
    print(f"\nYou can view the output at: /project1/background_render/OUT")

    return bg_container

# Execute the setup
if __name__ == "__main__":
    result = setup_background_render()
