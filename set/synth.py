import bpy
import bpycv
import cv2
import addon_utils
import numpy as np
import os

base_dir = "/scratch/gpfs/js5013/programs/prosthetic/set"
card_dir = f"{base_dir}/cards/"
bg_dir = f"{base_dir}/backgrounds/"
save_dir = f"{base_dir}/data/"
n_gen = 10
n_cards = 10
replace = False

## enable dynamic sky and import image as planes addons
addon_names = ["io_import_images_as_planes"]
for addon in addon_names:
    loaded_default, loaded_state = addon_utils.check(addon)
    if not loaded_state:
        addon_utils.enable(addon)

# delete everything
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete()

# get background cards
bg_ims = [bg_dir + f for f in os.listdir(bg_dir)]

# ixs = np.random.choice(np.arange(1, 82), size=n_cards, replace=replace)
ixs = np.arange(1, 82)
for ix in ixs:
    i = int(ix)  # weird but it doesn't work without this line...
    cname = f"card-{i}"
    path = f"{card_dir}/{cname}.jpg"
    bpy.ops.import_image.to_plane(files=[{"name": path}])
    card = bpy.data.objects[cname]
    card.location = (0, 0, 0.03)
    card.dimensions = (0.2, 0.4, 0)  # a big card!
    card["inst_id"] = i

sx = 0.35
sy = 0.55
locx = np.arange(-4 * sx, 5 * sx, sx)
locy = np.arange(-4 * sy, 5 * sy, sy)
xx, yy = np.meshgrid(locx, locy)
xx, yy = xx.ravel(), yy.ravel()
coords = np.vstack((xx, yy)).T


def add_bg_plane(fname):
    # add background plane
    # bpy.ops.mesh.primitive_plane_add(size=25)
    bpy.ops.import_image.to_plane(files=[{"name": fname}])
    plane = bpy.context.object
    plane.scale = (1.5, 1.5, 1)
    plane.location = (sx * 10, sy * 10, -1e-3)
    plane.modifiers.new("Array", "ARRAY")
    plane.modifiers["Array"].relative_offset_displace[0] = -1
    plane.modifiers["Array"].count = 7
    plane.modifiers.new("Array.001", "ARRAY")
    plane.modifiers["Array.001"].relative_offset_displace[0] = 0
    plane.modifiers["Array.001"].relative_offset_displace[1] = -1
    plane.modifiers["Array.001"].count = 7
    return plane


# add a light
light_data = bpy.data.lights.new("light", type="POINT")
light = bpy.data.objects.new("light", light_data)
bpy.context.collection.objects.link(light)
light.location = (1, 2, 1.5)  # meters away
light.data.energy = 120.0  # watts
light.data.shadow_soft_size = 0.2  # radius of lightbulb in m

# add a light
light_data2 = bpy.data.lights.new("light2", type="POINT")
light2 = bpy.data.objects.new("light", light_data2)
bpy.context.collection.objects.link(light2)

# make camera
cam_data = bpy.data.cameras.new("camera")
cam = bpy.data.objects.new("camera", cam_data)
bpy.context.collection.objects.link(cam)
cam.location = (-2, 2, 1.5)
cam.data.lens = 50


# always point at the center
bpy.ops.object.empty_add(
    type="CUBE", align="WORLD", location=(0.1, 0.1, 0.1), scale=(1, 1, 1)
)
empty = bpy.context.object
constraint = cam.constraints.new(type="TRACK_TO")
constraint.target = empty
# cam.data.dof.use_dof = True
# cam.data.dof.focus_object = empty
# cam.data.dof.aperture_fstop = 12
# cam.data.dof.aperture_blades = 9

scene = bpy.context.scene
scene.camera = cam
# scene.render.engine = 'BLENDER_EEVEE'
# scene.eevee.taa_render_samples = 64
scene.render.image_settings.file_format = "JPEG"
scene.render.engine = "CYCLES"
scene.cycles.device = "GPU"

scene.cycles.samples = 128
scene.cycles.use_denoising = True
scene.cycles.denoiser = "OPTIX"
scene.cycles.use_guiding = True
scene.cycles.guiding_training_samples = 64
scene.cycles.max_bounces = 8
scene.render.threads_mode = "AUTO"
scene.cycles.debug_use_spatial_splits = True
scene.render.use_persistent_data = True

for it in range(n_gen):
    try:
        plane.select_set(True)
        bpy.ops.object.delete()
    except:
        pass
    plane = add_bg_plane(np.random.choice(bg_ims))

    cam.location = (*np.random.normal(size=2), np.random.uniform(3, 7, size=1))
    cam.data.lens = np.random.uniform(28, 75)

    light.location = (*np.random.normal(size=2), np.random.uniform(1, 3, size=1))
    light.data.energy = np.random.uniform(200, 500)  # watts
    light.data.shadow_soft_size = (
        np.random.uniform(0, 2) + light.data.energy / 100
    )  # radius of lightbulb in m
    light.data.color = np.random.uniform(0.8, 1, size=3)  # random color, bright-ish

    light2.location = (*np.random.normal(size=2), np.random.uniform(1, 3, size=1))
    light2.data.energy = np.random.uniform(200, 500)  # watts
    light2.data.shadow_soft_size = (
        np.random.uniform(0, 2) + light.data.energy / 100 - 0.5
    )  # radius of lightbulb in m
    light2.data.color = np.random.uniform(0.8, 1, size=3)  # random color, bright-ish

    randix = np.random.choice(ixs.size, size=ixs.size, replace=False)
    for ix in ixs:
        cname = f"card-{ix}"
        card = bpy.data.objects[cname]
        card.rotation_euler[2] = np.random.normal(0, 0.12)  # random rotation
        card.location[:2] = coords[randix[ix - 1]] + np.random.normal(0.0, 0.01, size=2)
        card.location[2] = np.random.uniform(0.000017, 0.00024)  # random height

    result = bpycv.render_data()
    inst = result["inst"]

    out_string = ""

    for ix in ixs:
        y, x = np.where(inst == ix)
        try:
            x_width, y_width = x.max() - x.min(), y.max() - y.min()
            x_center, y_center = (x.min() + x.max()) / 2, (y.min() + y.max()) / 2
            x_width, x_center = x_width / inst.shape[1], x_center / inst.shape[1]
            y_width, y_center = y_width / inst.shape[0], y_center / inst.shape[0]
            out_string += f"{ix} {x_center} {y_center} {x_width} {y_width}\n"
        except:
            pass

    with open(f"{save_dir}/ims/im-{it}.txt", "w") as f:
        f.write(out_string)

    cv2.imwrite(f"{save_dir}/ims/im-{it}.jpg", result["image"][..., ::-1])
    cv2.imwrite(f"{save_dir}/inst/inst-{it}.jpg", inst * 255 / inst.max())
